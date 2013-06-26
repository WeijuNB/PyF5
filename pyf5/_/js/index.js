
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

function FolderSegment(name, path) {
    var self = this;

    self.name = ko.observable(name);
    self.absolutePath = ko.observable(path);
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

    self.queryProjects = function (init) {
        queryAPIScript('project.list', {}, function (data) {
            self.projects.removeAll();
            $(data['projects']).each(function (i, obj) {
                self.projects.push(new ProjectModel(obj.path, obj.isCurrent));
            });
            if (init) self.selectProject(self.currentProject());
        });
    };

    self.selectProject = function (project) {
        queryAPIScript('project.setCurrent', {path: project.path()}, function (data) {
            self.currentProject(project);
            self.queryFileList(project.path());
            self.queryBlockPaths(project.path());
            $('#projects .op a').tooltip();
            $('#script-hint-link').tooltip();
            if ($.cookie('show-script-hint') != 'false') {
                self.showScriptHint();
            } else {
                self.hideScriptHint();
            }
            self.folderSegments.removeAll();
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
        queryAPIScript('project.remove', {'path': project.path()}, function (data) {
            self.projects.remove(project);
        })
    };

    self.addProjectWithPath = function (path) {
        path = path.replace(/\\/g, '/');
        var $input = $("#new-path-input");
        var $btn = $('#project-add-btn');
        queryAPIScript('project.add', {path: path}, function (data) {
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
        self.files.removeAll();

        queryAPIScript('os.listDir', {path: path}, function (data) {
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
        var currentPath = rootPath;
        self.folderSegments.removeAll();
        $(relPath.split('/')).each(function (i, segment) {
            if (currentPath[currentPath.length-1] != '/') {
                currentPath += '/';
            }
            currentPath += segment;
            if (segment) {
                self.folderSegments.push(new FolderSegment(segment, currentPath));
            }
        })
    };

    self.clickFile = function (file, event) {
        if (file.type() == 'DIR') {
            self.enterFolder(file.absolutePath());
            return false;
        }
        return true;
    };

    self.clickFolderSegment = function (obj, event) {
        if (obj.path) {
            self.enterFolder('');
        } else {
            self.enterFolder(obj.absolutePath());
        }
    };

    self.enterFolder = function (absolutePath) {
        self.refreshFolderSegments(absolutePath);

        var foundSegment = null;
        var foundIndex = -1;
        $(self.folderSegments()).each(function (i, segment) {
           if (segment.absolutePath() == absolutePath) {
               foundSegment = segment;
               foundIndex = i;
               return false;
           }
        });

        if (foundSegment) {
            self.queryFileList(foundSegment.absolutePath());
        } else {
            self.queryFileList(self.currentProject().path());
        }
        self.folderSegments.splice(foundIndex + 1);
    };

    // ========================== blockPath
    self.queryBlockPaths = function (projectPath) {
        queryAPIScript('project.blockPaths', {'projectPath': self.currentProject().path()}, function (data) {
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
        queryAPIScript('project.toggleBlockPath', params, function (data) {
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
    vm.queryProjects(true);
    $('#host').text(
        !location.port || location.port == 80 ? '127.0.0.1' : ('127.0.0.1:' + location.port)
    );
});