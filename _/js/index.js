
function queryAPI(cmd, params, callback, error_callback) {
    var url = '/_/api?';
    var callback_name = '_jsonp_callback_' + parseInt(Math.random() * 100000000000);
    var param_pairs = ['cmd=' + cmd, 'callback=' + callback_name];

    for (var key in params) {
        param_pairs.push(key + '=' + encodeURIComponent(params[key]));
    }
    url += param_pairs.join('&');

    window[callback_name] = function(data) {
        delete window[callback_name];
        if (data.status == 'ok') {
            callback(data);
        } else if (error_callback) {
            error_callback(data);
        } else {
            alert(data['message']);
        }
    };
    $.getScript(url)
        .fail(function(){
            if (window[callback_name]) {
                delete window[callback_name];
            }
        });
}


function ProjectModel(path, isCurrent) {
    var self = this;

    self.path = ko.observable(path);
    self.isCurrent = ko.observable(isCurrent);
}

function FileModel(data) {
    var self = this;

    self.name = ko.observable(data['name']);
    self.type = ko.observable(data['type']);
}

function ProjectsViewModel() {
    var self = this;

    self.projects = ko.observableArray([]);
    self.currentProject = ko.computed(function() {
        var _currentProject = null;
        $(self.projects()).each(function(i, project) {
            if (project.isCurrent()) {
                _currentProject = project;
                return false;
            }
        });
        return _currentProject;
    });

    self.folderSegments = ko.observableArray([]);
    self.files = ko.observableArray([]);

    self.clickFile = function(data, event) {
        if (data.type() == 'DIR') {
            self.folderSegments.push(data.name());
            self.enterFolderSegment(data.name());
        }
    };

    self.clickBreadCrumb = function(data, event) {
        console.log('clickBreakCrumb', data, typeof data);
        if (typeof data == 'object') {
            self.enterFolderSegment('');
        } else {
            self.enterFolderSegment(data);
        }
    };

    self.enterFolderSegment = function (name) {
        var path = self.currentProject().path();
        var matched_index = -1;
        $(self.folderSegments()).each(function(i, segment) {
            path += ('/' + segment);
            if (name == segment) {
                matched_index = i;
                return false;
            }
        });
        if (matched_index > -1) {
            self.queryFileList(path);
        } else {
            self.queryFileList(self.currentProject().path());
        }
        self.folderSegments.splice(matched_index+1);
    };

    self.queryFileList = function(path) {
        queryAPI('os.listDir', {path:path}, function(data) {
            self.files.removeAll();
            $(data['list']).each(function(i, obj) {
                self.files.push(new FileModel(obj));
            });
        });
    };

    self.selectProject = function(project) {
        if (project != self.currentProject()) {
//            queryAPI('project.setCurrent', {path:project.path()}, function(data) {
                $(self.projects()).each(function(i, project) {
                    project.isCurrent(false);
                });
                project.isCurrent(true);
                self.queryFileList(project.path());
//            })
        }
    };

    self.selectProjectWithPath = function(path) {
        $(self.projects()).each(function(i, project) {
            if (project.path() == path) {
                self.selectProject(project);
                return false;
            }
        });
    };

    self.updateProjects = function(project_objects) {
        self.projects.removeAll();
        $(project_objects).each(function(i, obj) {
            self.projects.push(new ProjectModel(obj.path, obj.isCurrent));
        });
    };

    self.onSubmit = function(formElement) {
        var new_path = $("#new-path-input").val();
        if (new_path) {
            queryAPI('project.add', {path:new_path}, function(data) {
                self.updateProjects(data['objects']);
            });
        }
        return false;
    };
}

var vm = new ProjectsViewModel();

ko.applyBindings(vm);

$(function(){
    queryAPI('project.all', {}, function(data) {
        vm.updateProjects(data['projects']);
        queryAPI('project.getCurrent', {}, function(data) {
            vm.selectProjectWithPath(data.project.path);
        });
    });
});