function queryAPI(cmd, params, success_handler, error_handler) {
    var url = '/_/api?';
    var callback_name = '_jsonp_callback_' + parseInt(Math.random() * 100000000000);
    var param_pairs = ['cmd=' + cmd, 'callback=' + callback_name];

    for (var key in params) {
        param_pairs.push(key + '=' + encodeURIComponent(params[key]));
    }
    url += param_pairs.join('&');

    window[callback_name] = function (data) {
        window[callback_name] = undefined;
        if (data.status == 'ok') {
            success_handler(data);
        } else if (error_handler) {
            error_handler(data);
        } else {
            alert(data['message']);
        }
    };
    $.getScript(url)
        .fail(function () {
            if (window[callback_name]) {
                window[callback_name] = undefined;
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

    self.currentProject = ko.computed({
        read: function () {
            var _currentProject = null;
            $(self.projects()).each(function (i, project) {
                if (project.isCurrent()) {
                    _currentProject = project;
                    return false;
                }
            });
            return _currentProject;
        },
        write: function(project) {
            if (project != self.currentProject()) {
                $(self.projects()).each(function(i, item) {
                    if (item == project) {
                        project.isCurrent(true);
                    } else {
                        item.isCurrent(false)
                    }
                });
            }
        },
        owner: self
    });
    self.blockPaths = ko.observableArray([]);
    self.folderSegments = ko.observableArray([]);
    self.files = ko.observableArray([]);

    // projects ===============================================
    self.currentProject.subscribe(function(newProject) {
        if (newProject) {
            self.queryFileList(newProject.path());
            self.queryBlockPaths(newProject.path());
            $('#projects .op a').tooltip();
            $('#script-hint-link').tooltip();
            if ($.cookie('show-script-hint') != 'false') {
                self.showScriptHint();
            } else {
                self.hideScriptHint();
            }
        }
    });

    self.findProject = function(path) {
        var foundProject = null;
        $(self.projects()).each(function (i, project) {
            if (project.path() == path) {
                foundProject = project;
                return false;
            }
        });
        return foundProject;
    };

    self.queryProjects = function () {
        queryAPI('project.list', {}, function (data) {
            self.projects.removeAll();
            $(data['projects']).each(function (i, obj) {
                self.projects.push(new ProjectModel(obj.path, obj.isCurrent));
            });
        });
    };

    self.selectProject = function (project) {
        queryAPI('project.setCurrent', {path: project.path()}, function (data) {
            self.currentProject(project);
        })
    };

    self.selectProjectWithPath = function (path) {
        var project = self.findProject(path);
        if (project) {
            self.selectProject(project);
        }
    };

    self.askRemoveProject = function (project) {
        if (confirm('是否确认【删除】该项目?')) {
            self.removeProject(project);
        }
    };

    self.removeProject = function (project) {
        queryAPI('project.remove', {'path': project.path()}, function (data) {
            self.projects.remove(project);
        })
    };

    self.addProjectWithPath = function (path) {
        var $input = $("#new-path-input");
        var $btn = $('#project-add-btn');
        queryAPI('project.add', {path: path}, function (data) {
            self.projects.push(new ProjectModel(path, false));
            $input.attr('disabled', false).val('');
            $btn.attr('disabled', false);
        }, function (data) {
            alert(data['message']);
            $input.attr('disabled', false);
            $btn.attr('disabled', false);
        });
    };

    self.onSubmitProjectPath = function (formElement) {
        var $input = $("#new-path-input");
        var $btn = $('#project-add-btn');
        $input.val($.trim($input.val()));
        var projectPath = $input.val();
        if (projectPath) {
            self.addProjectWithPath(projectPath);
        } else {
            alert('请输入路径');
        }
        return false;
    };

    // ================================= Files
    self.queryFileList = function (path) {
        queryAPI('os.listDir', {path: path}, function (data) {
            self.files.removeAll();
            $(data['list']).each(function (i, obj) {
                var file = new FileModel(obj);
                var relPath = file.absolutePath().replace(self.currentProject().path(), '');
                file.url(/.*?:\/\/.*?\//.exec(location.href)[0] + relPath.substr(1));
                self.files.push(file);
            });
            self.refreshFilesBlockStatus();
        });
    };

    self.refreshFolderSegments = function (path) {
        var rootPath = self.currentProject().path();
        var relPath = path.replace(rootPath, '');
        self.folderSegments.removeAll();
        $(relPath.split('/')).each(function (i, segment) {
            if (segment) {
                self.folderSegments.push(segment);
            }
        })
    };

    self.clickFile = function (file, event) {
        if (file.type() == 'DIR') {
            self.refreshFolderSegments(file.absolutePath())
            self.enterFolderSegment(file.name());
            return false;
        }
        return true;
    };

    self.clickFolderSegment = function (data, event) {
        if (typeof data == 'object') {
            self.enterFolderSegment('');
        } else {
            self.enterFolderSegment(data);
        }
    };

    self.enterFolderSegment = function (name) {
        var path = self.currentProject().path();
        var matched_index = -1;
        $(self.folderSegments()).each(function (i, segment) {
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
        self.folderSegments.splice(matched_index + 1);
    };

    // ========================== blockPath
    self.queryBlockPaths = function (projectPath) {
        queryAPI('project.blockPaths', {'projectPath': self.currentProject().path()}, function (data) {
            self.blockPaths(data['blockPaths']);
            self.refreshFilesBlockStatus();
        });
    };

    self.refreshFilesBlockStatus = function () {
        $(self.files()).each(function (i, file) {
            if (self.blockPaths().indexOf(file.absolutePath()) > -1) {
                file.isBlocked(true);
            } else {
                file.isBlocked(false);
            }
        });
        $('#file-list a.op').tooltip();
    };

    self.toggleBlock = function (data, event) {
        var blocked = self.blockPaths().indexOf(data.absolutePath()) > -1;
        var params = {
            projectPath: self.currentProject().path(),
            blockPath: data.absolutePath(),
            action: blocked ? 'off' : 'on'
        };
        queryAPI('project.toggleBlockPath', params, function (data) {
            self.queryBlockPaths(self.currentProject().path());
        });
    };

    // =================================== misc
    self.showScriptHint = function() {
        $('#script-hint-link').hide();
        $('#script-hint').show();
        $.cookie('show-script-hint', true);
    };

    self.hideScriptHint = function() {
        $('#script-hint-link').show();
        $('#script-hint').hide();
        $.cookie('show-script-hint', false);
    }

}

var vm = new ProjectsViewModel();

ko.applyBindings(vm);

$(function () {
    vm.queryProjects();
    $('#host').text(
        !location.port || location.port == 80 ? '127.0.0.1' : ('127.0.0.1:' + location.port)
    );
});