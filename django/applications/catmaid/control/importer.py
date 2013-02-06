import json
import glob
import os.path
import yaml

from django import forms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, loader
from django.contrib.formtools.wizard.views import SessionWizardView
from django.shortcuts import render_to_response
from django.utils.datastructures import SortedDict

from guardian.models import Permission, User, Group
from guardian.shortcuts import get_perms_for_model, assign

from catmaid.models import Project, Stack, ProjectStack, Overlay, Double3D

from catmaid.control.common import urljoin

TEMPLATES = {"pathsettings": "catmaid/import/setup_path.html",
             "projectselection": "catmaid/import/setup_projects.html",
             "confirmation": "catmaid/import/confirmation.html"}

info_file_name = "project.yaml"
datafolder_setting = "CATMAID_IMPORT_PATH"
base_url_setting = "CATMAID_IMPORT_URL"

class ImageBaseMixin:
    def set_image_fields(self, info_object, project_url, data_folder, needs_zoom):
        """ Sets the image_base, num_zoom_levels, file_extension fields
        of the calling object. Favor a URL field, if there is one. A URL
        field, however, also requires the existence of the
        'fileextension' and and 'zoomlevels' field.
        """
        if 'url' in info_object:
            self.image_base = info_object['url']
            if needs_zoom:
                self.num_zoom_levels = info_object['zoomlevels']
            self.file_extension = info_object['fileextension']
        else:
            # The image base of a stack is the combination of the
            # project URL and the stack's folder name.
            folder = info_object['folder']
            self.image_base = urljoin(project_url, folder)
            # Favor 'zoomlevel' and 'fileextension' fields, if
            # available, but try to find this information if thosa
            # fields are not present.
            zoom_available = 'zoomlevels' in info_object
            ext_available = 'fileextension' in info_object
            if zoom_available and needs_zoom:
                self.num_zoom_levels = info_object['zoomlevels']
            if ext_available:
                self.file_extension = info_object['fileextension']
            # Only retrieve file extension and zoom level if one of
            # them is not available in the stack definition.
            if (not zoom_available and needs_zoom) or not ext_available:
                file_ext, zoom_levels = find_zoom_levels_and_file_ext(
                    data_folder, folder, needs_zoom )
                # If there is no zoom level provided, use the found one
                if not zoom_available and needs_zoom:
                    self.num_zoom_levels = zoom_levels
                # If there is no file extension level provided, use the
                # found one
                if not ext_available:
                    self.file_extension = file_ext
        # Make sure the image base has a trailing slash, because this is expected
        if self.image_base[-1] != '/':
            self.image_base = self.image_base + '/'

class PreOverlay(ImageBaseMixin):
    def __init__(self, info_object, project_url, data_folder):
        self.name = info_object['name']
        # Set default opacity, if available, defaulting to 0
        if 'defaultopacity' in info_object:
            self.default_opacity = info_object['defaultopacity']
        else:
            self.default_opacity = 0
        # Set 'image_base', 'num_zoom_levels' and 'fileextension'
        self.set_image_fields(info_object, project_url, data_folder, False)

class PreStack(ImageBaseMixin):
    def __init__(self, info_object, project_url, data_folder, only_unknown):
        self.name = info_object['name']
        # Set 'image_base', 'num_zoom_levels' and 'fileextension'
        self.set_image_fields(info_object, project_url, data_folder, True)
        # The 'dimension', 'resolution' and 'metadata' fields should
        # have every stack.
        self.dimension = info_object['dimension']
        self.resolution = info_object['resolution']
        self.metadata = info_object['metadata'] if 'metadata' in info_object else ""
        # Add overlays to the stack, if those are declared
        self.overlays = []
        if 'overlays' in info_object:
            for overlay in info_object['overlays']:
                self.overlays.append(PreOverlay(overlay, project_url, data_folder))

        # Test if this stack is already known
        if only_unknown:
            num_same_image_base = Stack.objects.filter(image_base=self.image_base).count()
            self.already_known = (num_same_image_base > 0)

class PreProject:
    def __init__(self, info_file, project_url, data_folder, only_unknown):
        self.info_file = info_file
        info = yaml.load(open(info_file))
        p = info['project']
        self.name = p['name']
        self.stacks = []
        self.has_been_imported = False
        self.import_status = None
        for s in p['stacks']:
            self.stacks.append( PreStack( s, project_url, data_folder, only_unknown ) )
        if only_unknown:
            # Mark this project as already known if all stacks are already known
            already_known_stacks = 0
            for s in self.stacks:
                if s.already_known:
                    already_known_stacks = already_known_stacks + 1
            self.already_known = (already_known_stacks == len(self.stacks))

def find_zoom_levels_and_file_ext( base_folder, stack_folder, needs_zoom=True ):
    """ Looks at the first file of the first zoom level and
    finds out what the file extension as well as the maximum
    zoom level is.
    """
    # Make sure the base path, doesn't start with a separator
    if base_folder[0] == os.sep:
        base_folder = base_folder[1:]
    # Build paths
    datafolder_path = getattr(settings, datafolder_setting)
    project_path = os.path.join(datafolder_path, base_folder)
    stack_path = os.path.join(project_path, stack_folder)
    slice_zero_path = os.path.join(stack_path, "0")
    filter_path = os.path.join(slice_zero_path, "0_0_0.*")
    # Look for 0/0_0_0.* file
    found_file = None
    for current_file in glob.glob( filter_path ):
        if os.path.isdir( current_file ):
            continue
        found_file = current_file
        break
    # Give up if we didn't find something
    if found_file is None:
        return (None, None)
    # Find extension
    file_ext = os.path.splitext(found_file)[1][1:]
    # Look for zoom levels
    zoom_level = 1
    if needs_zoom:
        while True:
            file_name = "0_0_" + str(zoom_level) + "." + file_ext
            path = os.path.join(slice_zero_path, file_name)
            if os.path.exists(path):
                zoom_level = zoom_level + 1
            else:
                zoom_level = zoom_level - 1
                break
    return (file_ext, zoom_level)

def find_project_folders(image_base, path, filter_term, only_unknown, depth=1):
    """ Finds projects in a folder structure by testing for the precense of an
    info/project YAML file.
    """
    dirs = []
    projects = {}
    not_readable = []
    for current_file in glob.glob( os.path.join(path, filter_term) ):
        if os.path.isdir(current_file):
            # Check if the folder has a info file
            info_file = os.path.join(current_file, info_file_name)
            if os.path.exists(info_file):
                short_name = current_file.replace(settings.CATMAID_IMPORT_PATH, "")
                # Check if this folder is already known by testing if
                # there is a stack with the same image base as a subfolder
                # would have.
                try:
                    # Make sure we have slashes in our directery URL part
                    url_dir = short_name
                    if os.sep != '/':
                        url_dir = url_dir.replace("\\", "/")
                    project_url = urljoin(image_base, url_dir)
                    project = PreProject( info_file, project_url, short_name, only_unknown )
                    if only_unknown and project.already_known:
                        continue
                    else:
                        projects[current_file] = project
                        # Remember this project if it isn't available yet
                        dirs.append( (current_file, short_name) )
                except Exception as e:
                    not_readable.append( (info_file, e) )
            elif depth > 1:
                # Recurse in subdir if requested
                dirs = dirs + find_files( current_file, depth - 1)
    return (dirs, projects, not_readable)

class ImportingWizard(SessionWizardView):
    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]

    def get_form(self, step=None, data=None, files=None):
        form = super(ImportingWizard, self).get_form(step, data, files)
        current_step = step or self.steps.current
        if current_step == 'pathsettings':
            pass
            # Pre-populate base URL field with settings variable, if available
            if hasattr(settings, base_url_setting):
                form.fields['base_url'].initial = getattr(settings, base_url_setting)
        elif current_step == 'projectselection':
            # Get the cleaned data from first step
            path = self.get_cleaned_data_for_step('pathsettings')['relative_path']
            filter_term = self.get_cleaned_data_for_step('pathsettings')['filter_term']
            only_unknown = self.get_cleaned_data_for_step('pathsettings')['only_unknown_projects']
            base_url = self.get_cleaned_data_for_step('pathsettings')['base_url']
            # Get all folders that match the selected criteria
            data_dir = os.path.join(settings.CATMAID_IMPORT_PATH, path)
            if data_dir[-1] != os.sep:
                data_dir = data_dir + os.sep
            if len(filter_term) == "":
                filter_term = "*"
            folders, projects, not_readable = find_project_folders(
                base_url, data_dir, filter_term, only_unknown)
            # Sort the folders (wrt. short name) to be better readable
            folders = sorted(folders, key=lambda folder: folder[1])
            # Save these settings in the form
            form.folders = folders
            form.not_readable = not_readable
            self.projects = projects
            # Update the folder list and select all by default
            form.fields['projects'].choices = folders
            form.fields['projects'].initial = [f[0] for f in folders]
            # Get the available permissions and update the list
            group_permissions = get_group_permissions(Project)
            form.group_permissions = group_permissions
            group_perm_tuples = get_group_permission_tuples(group_permissions)
            form.fields['group_permissions'].choices = group_perm_tuples
        return form

    def get_context_data(self, form, **kwargs):
        context = super(ImportingWizard, self).get_context_data(form=form, **kwargs)

        if self.steps:
            if self.steps.current == 'pathsettings':
                datafolder_missing = not hasattr(settings, datafolder_setting)
                base_url_missing = not hasattr(settings, base_url_setting)
                context.update({
                    'datafolder_setting': datafolder_setting,
                    'datafolder_missing': datafolder_missing,
                    'base_url_setting': base_url_setting,
                    'base_url_missing': base_url_missing,
                })
            elif self.steps.current == 'projectselection':
                context.update({
                    'folders': form.folders,
                    'not_readable': form.not_readable,
                })
            elif self.steps.current == 'confirmation':
                # Selected projects
                selected_paths = self.get_cleaned_data_for_step('projectselection')['projects']
                selected_projects = [ self.projects[p] for p in selected_paths ]
                # Tags
                tags = self.get_cleaned_data_for_step('projectselection')['tags']
                if len(tags.strip()) == 0:
                    tags = []
                else:
                    tags = [t.strip() for t in tags.split(',')]
                # Permissions
                group_permissions = self.get_cleaned_data_for_step(
                    'projectselection')['group_permissions']
                group_permissions = get_permissions_from_selection( group_permissions )
                # Other settings
                max_num_stacks = 0
                tile_width = self.get_cleaned_data_for_step('projectselection')['tile_width']
                tile_height = self.get_cleaned_data_for_step('projectselection')['tile_height']
                for p in selected_projects:
                    if len(p.stacks) > max_num_stacks:
                        max_num_stacks = len(p.stacks)
                context.update({
                    'projects': selected_projects,
                    'max_num_stacks': max_num_stacks,
                    'tags': tags,
                    'group_permissions': group_permissions,
                    'tile_width': tile_width,
                    'tile_height': tile_height,
                })

        context.update({
            'title': "Importer",
            'settings': settings
        })

        return context

    def done(self, form_list, **kwargs):
        """ Will add the selected projects.
        """
        # Find selected projects
        selected_paths = self.get_cleaned_data_for_step('projectselection')['projects']
        selected_projects = [ self.projects[p] for p in selected_paths ]
        # Get permissions
        group_permissions = self.get_cleaned_data_for_step(
            'projectselection')['group_permissions']
        group_permissions = get_permissions_from_selection( group_permissions )
        # Tags
        tags = self.get_cleaned_data_for_step('projectselection')['tags']
        tags = [t.strip() for t in tags.split(',')]
        # Get remaining properties
        make_public = self.get_cleaned_data_for_step('projectselection')['make_projects_public']
        tile_width = self.get_cleaned_data_for_step('projectselection')['tile_width']
        tile_height = self.get_cleaned_data_for_step('projectselection')['tile_height']
        tile_source_type = 1
        imported_projects, not_imported_projects = import_projects(
            selected_projects, make_public, tags, group_permissions,
            tile_width, tile_height, tile_source_type)
        # Show final page
        return render_to_response('catmaid/import/done.html', {
            'projects': selected_projects,
            'imported_projects': imported_projects,
            'not_imported_projects': not_imported_projects,
        })

def importer_admin_view(request, *args, **kwargs):
    """ Wrapps the class based ImportingWizard view in a
    function based view.
    """
    forms = [("pathsettings", DataFileForm),
             ("projectselection", ProjectSelectionForm),
             ("confirmation", ConfirmationForm)]
    view = ImportingWizard.as_view(forms)
    return view(request)

def importer_finish(request):
    return render_to_response('catmaid/import/done.html', {})

def get_groups_with_perms_cls(cls, attach_perms=False):
    """ This is a stightly adapted version of guardians
    group retrieval. It doesn't need an object instance.
    """
    ctype = ContentType.objects.get_for_model(cls)
    if not attach_perms:
        groups = Group.objects.filter(
            groupobjectpermission__content_type=ctype).distinct()
        return groups
    else:
        groups = {}
        for group in get_groups_with_perms_cls(cls):
            if not group in groups:
                groups[group] = get_perms_for_model(cls)
        return groups

def get_group_permissions(cls):
    groups_perms = get_groups_with_perms_cls(cls, True)
    groups_perms = SortedDict(groups_perms)
    groups_perms.keyOrder.sort(key=lambda group: group.name)
    return groups_perms

def get_group_permission_tuples(groups_perms):
    """ Out of list of (group, [permissions] tuples, produce a
    list of tuples, each of the form
    (<group_id>_<perm_codename>, <group_name> | <parm_name>)
    """
    tuples = []
    for g in groups_perms:
        for p in groups_perms[g]:
            pg_id = str(g.id) + "_" + str(p.id)
            pg_title = g.name + " | " + p.name
            tuples.append( (pg_id, pg_title) )
    return tuples

def get_permissions_from_selection(selection):
    permission_list = []
    for perm in selection:
        group_id = perm[:perm.index('_')]
        group = Group.objects.filter(id=group_id)[0]
        perm_id = perm[perm.index('_')+1:]
        perm = Permission.objects.filter(id=perm_id)[0]
        permission_list.append( (group, perm) )
    return permission_list

class DataFileForm(forms.Form):
    """ A form to select basic properties on the data to be
    imported. Path and filter constraints can be set here.
    """
    relative_path = forms.CharField(required=False,
        widget=forms.TextInput(attrs={'size':'40'}),
        help_text="This path is <em>relative</em> to the data folder in use.")
    filter_term = forms.CharField(initial="*", required=False,
        widget=forms.TextInput(attrs={'size':'40'}),
        help_text="You can apply a <em>glob filter</em> to the projects found \
                   in your data folder.")
    only_unknown_projects = forms.BooleanField(initial=True, required=False,
        help_text="A project is marked as <em>known</em> if (and only if) \
                   all of its stacks are already known to the CATMAID instance.")
    base_url = forms.CharField(required=True,
        widget=forms.TextInput(attrs={'size':'40'}),
        help_text="The <em>base URL</em> should give read access to the data \
                   folder in use.")

class ProjectSelectionForm(forms.Form):
    """ A form to select projects to import out of the
    available projects.
    """
    # A checkbox for each project, checked by default
    projects = forms.MultipleChoiceField(required=False,
        widget=forms.CheckboxSelectMultiple(),
        help_text="Only selected projects will be imported.")
    tags = forms.CharField(initial="", required=False,
        help_text="A comma separated list of unquoted tags.")
    tile_width = forms.IntegerField(initial=256,
        help_text="The width of one tile in <em>pixel</em>.")
    tile_height = forms.IntegerField(initial=256,
        help_text="The height of one tile in <em>pixel</em>.")
    make_projects_public = forms.BooleanField(initial=False,
        required=False, help_text="If made public, a project \
        can be seen without being logged in.")
    group_permissions = forms.MultipleChoiceField(
        widget=forms.SelectMultiple(attrs={'size':'10'}),
        help_text="The selected <em>group/permission combination</em> \
                   will be assigned to every project.")

class ConfirmationForm(forms.Form):
    """ A form to confirm the selection and settings of the
    projects that are about to be imported.
    """
    something = forms.CharField(initial="", required=False)

def import_projects( pre_projects, make_public, tags, permissions,
    tile_width, tile_height, tile_source_type ):
    """ Creates real CATMAID projects out of the PreProject objects
    and imports them into CATMAID.
    """
    imported = []
    not_imported = []
    for pp in pre_projects:
        try:
            # Create stacks and add them to project
            stacks = []
            for s in pp.stacks:
                stack = Stack.objects.create(
                    title=s.name,
                    dimension=s.dimension,
                    resolution=s.resolution,
                    image_base=s.image_base,
                    num_zoom_levels=s.num_zoom_levels,
                    file_extension=s.file_extension,
                    tile_width=tile_width,
                    tile_height=tile_height,
                    tile_source_type=tile_source_type,
                    metadata=s.metadata)
                stacks.append( stack )
                # Add overlays of this stack
                for o in s.overlays:
                    Overlay.objects.create(
                        title=o.name,
                        stack=stack,
                        image_base=o.image_base,
                        default_opacity=o.default_opacity,
                        file_extension=o.file_extension,
                        tile_width=tile_width,
                        tile_height=tile_height,
                        tile_source_type=tile_source_type)
            # Create new project
            p = Project.objects.create(
                title=pp.name,
                public=make_public)
            # Assig permissions to project
            assigned_permissions = []
            for user_or_group, perm in permissions:
                assigned_perm = assign( perm.codename, user_or_group, p )
                assigned_permissions.append( assigned_perm )
            # Tag the project
            p.tags.add( *tags )
            # Add stacks to project
            for s in stacks:
                trln = Double3D()
                ps = ProjectStack.objects.create(
                    project=p, stack=s, translation=trln)
            # Save and remember this project
            p.save()
            imported.append( pp )
        except Exception as e:
            not_imported.append( (pp, e) )

    return (imported, not_imported)
