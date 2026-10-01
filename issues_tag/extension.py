"""Lifecycle and the Issues menu entry."""
import asyncio
import inspect
from contextlib import contextmanager
from pathlib import Path

import omni.ext
from omni.kit.menu.utils import MenuItemDescription, add_menu_items, remove_menu_items

from .service import IssueService

_service = None


def get_runtime_service():
    return _service


class IssuesExtension(omni.ext.IExt):
    """Manager-owned registration; pending work belongs to the detached controller."""
    def on_startup(self, ext_id):
        self._controller = IssuesController()
        self._controller.on_startup(ext_id)

    def on_shutdown(self):
        controller = getattr(self, '_controller', None)
        self._controller = None
        if controller:
            controller.on_shutdown()


class IssuesController:
    def on_startup(self, ext_id):
        global _service
        self._service = None
        self._viewport = None
        self._markup = None
        self._window = None
        self._toolbar = None
        self._dialogs = []
        self._tasks = set()
        self._session = self._details = self._annotation = self._edit_task = None
        self._owned_views = {}
        self._annotation_retry = False
        self._annotation_target = None
        self._shutting_down = False
        self._menus = []
        try:
            self._service = IssueService()
            from .viewport import ViewportAdapter
            from .markup import MarkupAdapter
            self._viewport = ViewportAdapter(self._service)
            self._service.viewport = self._viewport
            self._viewport.start()
            self._markup = MarkupAdapter(self._service)
            self._markup.suppress_window_close = self._evidence_ui
            self._service.native_view_recaller = self._markup.restore_viewpoint
            from .toolbar import IssuesToolbarButton
            self._toolbar = IssuesToolbarButton(self.show)
            self._menus = [MenuItemDescription(name="Issues", onclick_fn=self.show)]
            add_menu_items(self._menus, "Window")
        except Exception as startup_error:
            try:
                self.on_shutdown()
            except Exception as cleanup_error:
                raise ExceptionGroup('Issues startup and rollback failed', [startup_error, cleanup_error]) from None
            raise
        _service = self._service

    def show(self):
        if self._shutting_down:
            return
        if self._window is None:
            from .window import IssuesWindow
            self._window = IssuesWindow(self._service, on_select=self.select_issue,
                on_create=self.begin_creation, on_import=lambda: self.file_dialog(False),
                on_export=lambda: self.file_dialog(True), on_error=self._dispatch)
            self._viewport.on_pin_clicked = lambda issue_id: self._dispatch(self.select_issue, issue_id)
        self._window.show()

    def _error(self, error):
        if self._details:
            self._details.set_error(str(error))
        elif self._window:
            self._window._error = str(error)
            self._window.refresh()

    def _dispatch(self, callback, *args):
        """Own every asynchronous UI action, including close/cancel while busy."""
        if self._shutting_down:
            return
        try:
            result = callback(*args)
            if not inspect.isawaitable(result):
                return result
        except Exception as error:
            self._error(error)
            return
        async def run():
            try:
                return await result
            except asyncio.CancelledError:
                raise
            except Exception as error:
                self._error(error)
        pending = run()
        try:
            # Kit's native UI callbacks run between asyncio ticks on its installed loop.
            task = asyncio.ensure_future(pending)
        except Exception as error:
            pending.close()
            if inspect.iscoroutine(result):
                result.close()
            self._error(error)
            return None
        self._tasks.add(task)
        def finished(done):
            self._tasks.discard(done)
            if done.cancelled() and inspect.iscoroutine(result):
                result.close()
        task.add_done_callback(finished)
        return task

    async def _operation(self, action, *args):
        current = asyncio.current_task()
        if self._shutting_down:
            return None
        if self._edit_task and self._edit_task is not current:
            self._error('Finish or cancel the current operation before starting another.')
            return None
        nested = self._edit_task is current
        self._edit_task = current
        try:
            if self._details:
                self._details.sync()
                self._details.set_error('')
                self._details.set_busy(True)
            elif self._window:
                self._window._error = ''
            return await action(*args)
        except Exception as error:
            self._error(error)
            return None
        finally:
            if not nested:
                self._edit_task = None
                if self._details:
                    self._details.set_busy(False)

    def _open_details(self, session):
        from .window import IssueDetailsWindow
        self._session = session
        self._annotation_retry = False
        self._annotation_target = None
        self._details = IssueDetailsWindow(session, self._service.list_types(),
            on_save=lambda: self._dispatch(self.save_details),
            on_cancel=lambda: self._dispatch(self.cancel_details),
            on_annotate=lambda: self._dispatch(self.annotate_details),
            on_replace=lambda: self._dispatch(self.replace_screenshot),
            on_comment_view=lambda view_id: self._dispatch(self.open_comment_view, view_id),
            on_open_review_view=lambda: self._dispatch(self.open_review_view),
            on_reattach=lambda: self._dispatch(self.reattach_pin),
            on_add_related=lambda: self._dispatch(self.add_selected_related),
            on_remove_related=lambda element: self._dispatch(self.remove_related, element),
            on_focus_related=lambda: self._dispatch(self.focus_related),
            on_capture_comment=lambda: self._dispatch(self.capture_comment_viewpoint),
            on_annotate_comment=lambda comment_id=None: self._dispatch(self.annotate_comment, comment_id),
            on_add_comment=lambda: self._dispatch(self.add_comment))

    async def begin_creation(self, decision=None):
        return await self._operation(self._begin_creation, decision)

    async def _begin_creation(self, decision):
        if not await self._resolve_details(decision):
            return None
        service = self._service
        stage, generation = service.stage, service.generation
        service.store.require_writable()
        self._window.set_placement_state(True, self._viewport.cancel_placement)
        try:
            anchor = await self._viewport.request_placement()
            if anchor is None:
                return None
            if service.stage != stage or service.generation != generation:
                raise ValueError('The scene changed during issue placement.')
            return await self._create_issue_from_pin(anchor)
        finally:
            if self._window:
                self._window.set_placement_state(False)

    async def _create_issue_from_pin(self, anchor):
        return await self._operation(self._prepare_creation, anchor)

    async def _prepare_creation(self, anchor):
        from .edit_session import IssueEditSession
        service, markup = self._service, self._markup
        window, viewport = markup._evidence_viewport()
        if self._viewport._placement_viewport != window.viewport_api:
            raise ValueError('Place the issue in the primary Viewport to add Markup evidence.')
        service.store.require_writable()
        self._open_details(IssueEditSession.create(service, anchor, service.list_types()[0], None))
        self._details.set_busy(True)
        self._viewport.restore(viewport.capture())
        record = await markup.capture_viewpoint()
        self._own(record)
        self._session.require_current(service)
        self._session.viewpoint = record
        await markup.begin(record)
        self._annotation = record
        return self._session

    def _own(self, record):
        self._owned_views[record.id] = record

    async def select_issue(self, issue_id, decision=None):
        return await self._operation(self._select_issue, issue_id, decision)

    async def _select_issue(self, issue_id, decision):
        from .edit_session import IssueEditSession
        if self._session and not self._session.is_new and self._session.record.id == issue_id:
            await self._open_review_view()
            return issue_id
        if not await self._resolve_details(decision):
            return None
        session = IssueEditSession.edit(self._service, issue_id)
        self._service.open_issue(issue_id)
        self._open_details(session)
        self._window.selected_issue_id = issue_id
        self._window.refresh()
        return issue_id

    @contextmanager
    def _evidence_ui(self, floating_windows):
        # Screenshot suppression hides floating windows; that is not a user close.
        details = self._details
        window = getattr(details, 'window', None)
        suppressed = window is not None and any(item is window for item in floating_windows)
        if suppressed:
            window.set_visibility_changed_fn(None)
        try:
            yield
        finally:
            if suppressed and self._details is details:
                window.set_visibility_changed_fn(details._visibility)

    async def _finish_annotation(self, save):
        record = self._annotation
        if record is not None:
            if self._annotation_retry and not save:
                self._annotation = None
                self._annotation_retry = False
                return
            try:
                if self._annotation_retry:
                    await self._markup.begin(record)
                task = asyncio.create_task(self._markup.finish(record, save=save))
                try:
                    updated = await asyncio.shield(task)
                except asyncio.CancelledError:
                    # finish() can be awaiting a native screenshot. Keep its owner alive.
                    while not task.done():
                        try:
                            await asyncio.shield(task)
                        except asyncio.CancelledError:
                            continue
                        except Exception:
                            break
                    if not task.cancelled():
                        task.exception()
                    raise
                if save:
                    self._set_evidence(self._annotation_target, updated)
                    self._own(updated)
            except BaseException:
                self._annotation_retry = True
                raise
            else:
                self._annotation = None
                self._annotation_retry = False

    async def annotate_details(self):
        return await self._operation(self._annotate_details)

    async def _annotate_details(self):
        if self._session:
            await self._annotate_evidence(self._session.viewpoint, None)

    def _set_evidence(self, target, record):
        if target is None:
            self._session.viewpoint = record
        elif target == 'pending':
            self._session.comment_viewpoint = record
        else:
            self._session.set_comment_viewpoint(target, record)

    async def _annotate_evidence(self, record, target):
        if record is None or (self._annotation and self._annotation_target == target):
            return
        session = self._session
        session.require_current(self._service)
        self._service.store.require_writable()
        await self._finish_annotation(True)
        if record.id not in self._owned_views:
            record = await self._markup.copy_for_edit(record)
            self._own(record)
        else:
            self._service.viewport.restore(record)
        session.require_current(self._service)
        await self._markup.begin(record)
        self._set_evidence(target, record)
        self._annotation, self._annotation_target = record, target

    async def annotate_comment(self, comment_id=None):
        async def annotate():
            session = self._session
            if session:
                record = session.comment_viewpoint if comment_id is None else session.comment_viewpoints[comment_id]
                await self._annotate_evidence(record, 'pending' if comment_id is None else comment_id)
        return await self._operation(annotate)

    async def capture_comment_viewpoint(self):
        async def capture():
            session = self._session
            if not session:
                return
            session.require_current(self._service)
            self._service.store.require_writable()
            await self._finish_annotation(True)
            record = await self._markup.capture_viewpoint()
            self._own(record)
            session.require_current(self._service)
            previous = session.comment_viewpoint
            session.comment_viewpoint = record
            if previous and previous.id in self._owned_views:
                self._discard_owned(previous)
        return await self._operation(capture)

    async def add_comment(self):
        async def add():
            if not self._session:
                return
            self._session.require_current(self._service)
            self._service.store.require_writable()
            await self._finish_annotation(True)
            comment_id = self._session.stage_comment(self._service)
            self._details.clear_comment()
            return comment_id
        return await self._operation(add)

    async def add_selected_related(self):
        async def add():
            from .elements import reference_for_prim
            self._session.require_current(self._service)
            self._service.store.require_writable()
            paths = self._service._context.get_selection().get_selected_prim_paths()
            if not paths:
                raise ValueError('Select model elements to add to this issue.')
            refs = tuple(reference_for_prim(self._service.stage, path) for path in paths)
            self._session.update(related_elements=tuple(dict.fromkeys(self._session.record.related_elements + refs)))
        return await self._operation(add)

    async def remove_related(self, element):
        async def remove():
            self._session.require_current(self._service)
            self._service.store.require_writable()
            self._session.update(related_elements=tuple(ref for ref in self._session.record.related_elements if ref != element))
        return await self._operation(remove)

    async def focus_related(self):
        async def focus():
            self._session.require_current(self._service)
            await self._finish_annotation(True)
            self._viewport.focus(self._session.record.related_elements)
        return await self._operation(focus)

    async def reattach_pin(self):
        async def reattach():
            session = self._session
            session.require_current(self._service)
            self._service.store.require_writable()
            await self._finish_annotation(True)
            self._window.set_placement_state(True, self._viewport.cancel_placement)
            try:
                anchor = await self._viewport.request_placement()
                if anchor is not None:
                    session.require_current(self._service)
                    session.update(anchor=anchor)
            finally:
                self._window.set_placement_state(False)
        return await self._operation(reattach)

    async def replace_screenshot(self):
        return await self._operation(self._replace_screenshot)

    async def _replace_screenshot(self):
        session = self._session
        if not session:
            return
        session.require_current(self._service)
        self._service.store.require_writable()
        await self._finish_annotation(True)
        replacement = await self._markup.capture_viewpoint()
        self._own(replacement)
        session.require_current(self._service)
        previous = session.viewpoint
        session.viewpoint = replacement
        if previous and previous.id in self._owned_views:
            self._discard_owned(previous)

    async def open_review_view(self):
        return await self._operation(self._open_review_view)

    async def _open_review_view(self):
        session = self._session
        if not session:
            return
        session.require_current(self._service)
        await self._finish_annotation(True)
        session.require_current(self._service)
        if session.viewpoint:
            self._service.restore_viewpoint(session.viewpoint)

    async def open_comment_view(self, view_id):
        async def open_view():
            self._session.require_current(self._service)
            await self._finish_annotation(True)
            staged = (self._session.viewpoint, self._session.comment_viewpoint, *self._session.comment_viewpoints.values())
            record = next((view for view in staged if view and view.id == view_id), None)
            self._service.restore_viewpoint(record or self._service.store.get_viewpoint(view_id))
        return await self._operation(open_view)

    async def save_details(self):
        return await self._operation(self._save_details)

    async def _save_details(self):
        session = self._session
        if not session:
            return None
        session.require_current(self._service)
        self._service.store.require_writable()
        if session.is_new and session.viewpoint is None:
            raise ValueError('Capture a screenshot before saving this new issue.')
        title = session.record.title.strip()
        if not title or len(title) > 255:
            raise ValueError('Enter an issue title of 1 to 255 characters.')
        if session.record.issue_type not in self._service.list_types():
            raise ValueError('Select a project issue type.')
        await self._finish_annotation(True)
        session.require_current(self._service)
        issue_id = self._service.commit_session(session)
        accepted = (session.viewpoint, session.comment_viewpoint, *session.comment_viewpoints.values())
        for viewpoint in accepted:
            if viewpoint:
                self._owned_views.pop(viewpoint.id, None)
        self._close_details()
        self._window.refresh()
        if issue_id not in self._window.visible_issue_ids:
            self._window.clear_filters()
        self._window.selected_issue_id = issue_id
        self._window.refresh()
        return issue_id

    async def _resolve_details(self, decision=None):
        if not self._session:
            return True
        self._details.sync()
        if self._session.dirty or self._annotation:
            if decision is None:
                from .issue_editor import DirtyDetailsDialog
                dialog = DirtyDetailsDialog()
                self._dialogs.append(dialog)
                try:
                    decision = await dialog.wait()
                finally:
                    dialog.destroy()
                    self._dialogs.remove(dialog)
            if decision == 'stay':
                return False
            if decision == 'save':
                return bool(await self._save_details())
            if decision != 'discard':
                return False
        try:
            await self._finish_annotation(False)
        except ValueError:
            if self._service.stage == self._session.stage and self._service.generation == self._session.generation:
                raise
            # Native finish has released its old owner. Never write the replacement scene.
        self._close_details()
        return True

    async def cancel_details(self, decision=None):
        if self._shutting_down:
            return False
        task = self._edit_task
        if task and task is not asyncio.current_task():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        return await self._operation(self._resolve_details, decision)

    def _discard_owned(self, record):
        session = self._session
        if self._markup.discard_viewpoint(record, session.stage, session.generation):
            self._owned_views.pop(record.id, None)

    def _close_details(self):
        for record in tuple(self._owned_views.values()):
            self._discard_owned(record)
        details, self._details = self._details, None
        self._session = self._annotation = None
        self._owned_views.clear()
        if details:
            details.destroy()

    def file_dialog(self, export):
        from omni.kit.window.filepicker import FilePickerDialog
        from .bcf import read_bcf, write_bcf, export_document, plan_import, apply_import
        from .import_window import ImportWindow
        def selected(filename, dirname):
            path = Path(dirname) / filename
            if export:
                if path.suffix.lower() != '.bcf':
                    path = path.with_suffix('.bcf')
                write_bcf(export_document(self._service.store), path)
            else:
                plan = plan_import(read_bcf(path), self._service.store)
                preview = ImportWindow(plan, lambda choices: apply_import(plan, choices, self._service))
                self._dialogs.append(preview)
            dialog.hide()
        dialog = FilePickerDialog('Export BCF' if export else 'Import BCF', apply_button_label='Export' if export else 'Preview',
                                  click_apply_handler=lambda filename, dirname: self._window._call(selected, filename, dirname))
        self._dialogs.append(dialog)
        dialog.show()

    def on_shutdown(self):
        global _service
        if getattr(self, '_shutting_down', False):
            return
        self._shutting_down = True
        if _service is getattr(self, '_service', None):
            _service = None
        tasks = set(getattr(self, '_tasks', ()))
        owner = getattr(self, '_edit_task', None)
        if owner:
            tasks.add(owner)
        tasks = [task for task in tasks if not task.done()]
        for task in tasks:
            task.cancel()
        if tasks:
            async def drain():
                await asyncio.gather(*tasks, return_exceptions=True)
                self._destroy_resources()
            pending = drain()
            try:
                self._shutdown_task = tasks[0].get_loop().create_task(pending)
            except BaseException:
                pending.close()
                raise
        else:
            self._destroy_resources()

    def _destroy_resources(self):
        service, self._service = getattr(self, '_service', None), None
        viewport, self._viewport = getattr(self, '_viewport', None), None
        markup, self._markup = getattr(self, '_markup', None), None
        window, self._window = getattr(self, '_window', None), None
        details, self._details = getattr(self, '_details', None), None
        toolbar, self._toolbar = getattr(self, '_toolbar', None), None
        menus, self._menus = getattr(self, '_menus', []), []
        dialogs, self._dialogs = getattr(self, '_dialogs', []), []
        self._session = self._annotation = self._edit_task = None
        self._owned_views = {}
        self._tasks = set()
        failures = []
        def clean(operation):
            try:
                operation()
            except Exception as error:
                failures.append(error)
        if menus:
            clean(lambda: remove_menu_items(menus, "Window"))
        for resource in (toolbar, details, window, *dialogs, markup, viewport):
            if resource:
                clean(resource.destroy)
        if service:
            if service.viewport is not None and service.viewport is not viewport:
                clean(service.viewport.destroy)
            service.viewport = None
            clean(service.destroy)
        if failures:
            raise ExceptionGroup('Issues cleanup failed', failures)
