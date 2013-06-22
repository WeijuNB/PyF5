
function queryAPI(cmd, params, success_handler, error_handler) {
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
            success_handler(data);
        } else if (error_handler) {
            error_handler(data);
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
    self.absolutePath = ko.observable(data['absolutePath']);

    self.isBlocked = ko.observable(false);
    self.url = ko.observable('');
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
    self.blockPaths = ko.observableArray([]);
    self.folderSegments = ko.observableArray([]);
    self.files = ko.observableArray([]);

    self.updateFilesBlockStatus = function() {
        console.log('update');
        $(self.files()).each(function(i, file) {
            if (self.blockPaths().indexOf(file.absolutePath()) > -1) {
                file.isBlocked(true);
            } else {
                file.isBlocked(false);
            }
        })
    };

    self.init = function() {
        queryAPI('project.all', {}, function(data) {
            self.updateProjects(data['projects']);
            queryAPI('project.getCurrent', {}, function(data) {
                if (data.project) {
                    self.selectProjectWithPath(data.project.path);
                }
            });
        });
    };

    self.clickFile = function(file, event) {
        console.log(ko.toJS(file));
        if (file.type() == 'DIR') {
            self.folderSegments.push(file.name());
            self.enterFolderSegment(file.name());
            return false;
        }
        return true;
    };

    self.toggleBlock = function(data, event) {
        var blocked = self.blockPaths().indexOf(data.absolutePath()) > -1;
        var params = {
            projectPath: self.currentProject().path(),
            blockPath: data.absolutePath(),
            action: blocked ? 'off' : 'on'
        };
        queryAPI('project.toggleBlockPath', params, function(data) {
            self.queryBlockPaths(self.currentProject().path());
        });
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
                console.log('add file', obj);
                var file = new FileModel(obj);
                self.files.push(file);
                file.url(/.*?:\/\/.*?\//.exec(location.href)[0] + self.folderSegments().join('/') + file.name());
            });
            self.updateFilesBlockStatus();
        });
    };
    self.queryBlockPaths = function(projectPath) {
        queryAPI('project.blockPaths', {'projectPath': self.currentProject().path()}, function(data) {
            self.blockPaths(data['blockPaths']);
            self.updateFilesBlockStatus();
        });
    };

    self.selectProject = function(project) {
        queryAPI('project.setCurrent', {path:project.path()}, function(data) {
            self.queryFileList(project.path());
            self.queryBlockPaths(project.path());
        })
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
    vm.init();
});