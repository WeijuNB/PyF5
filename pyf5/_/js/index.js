function joinPath(p1, p2) {
    var path = [p1 , p2].join('/');
    path = path.replace(/\/+/g, '/');
    return path;
}


function ProjectModel(data) {
    var self = this;

    self.path = ko.observable("");
    self.active = ko.observable(false);
    self.muteList = ko.observableArray([]);
    self.targetHost = ko.observable('');

    self.load = function (data) {
        self.path(data.path);
        self.active(data && data.active ? data.active : false);
        self.muteList(data && data.muteList ? data.muteList : []);
        self.targetHost(data && data.targetHost ? data.targetHost : '');
    };

    if (data) {
        self.load(data);
    }
}


function FileModel(data, project) {
    var self = this;

    self.name = ko.observable(data['name']);
    self.type = ko.observable(data['type']);
    self.absolutePath = ko.observable(data['absolutePath']);

    self.url = ko.computed(function () {
        var relPath = self.absolutePath().replace(project.path(), '');
        if (relPath && relPath[0] == '/') {
            relPath = relPath.substr(1);
        }
        return /.*?:\/\/.*?\//.exec(location.href)[0] + relPath;
    });

    self.isMute = ko.computed(function () {
        var mutePath;
        if (!project.muteList()) {
            return false;
        }
        for (var i = 0; i < project.muteList().length; i++) {
            mutePath = project.muteList()[i];
            if (self.absolutePath() == joinPath(project.path(), mutePath)) {
                return true;
            }
        }
        return false;
    });
}


function FolderSegment(name, path) {
    var self = this;

    self.name = ko.observable(name);
    self.absolutePath = ko.observable(path);
}


function ViewModel() {
    var self = this;

    self.hostText = ko.observable(!location.port || location.port == 80 ? '127.0.0.1' : ('127.0.0.1:' + location.port));

    self.projects = ko.observableArray([]);

    self.currentProject = ko.computed({
        read: function () {
            var project;
            for (var i = 0; i < self.projects().length; i += 1) {
                project = self.projects()[i];
                if (project.active()) {
                    return project
                }
            }
            return null;
        },
        write: function(activeProject) {
            var project;
            if (activeProject != self.currentProject()) {
                for (var i = 0; i < self.projects().length; i += 1) {
                    project = self.projects()[i];
                    if (project.path() != activeProject.path()) {
                        project.active(false);
                    } else {
                        project.active(true);
                    }
                }
            }
        },
        owner: self
    });
    self.currentProject.subscribe(function (newValue) {

    });

    self.folderSegments = ko.observableArray([]);
    self.files = ko.observableArray([]);

    // projects ===============================================
    self.findProject = function(path) {
        var project;
        for (var i = 0; i < self.projects().length; i += 1) {
            project = self.projects()[i];
            if (project.path() == path) {
                return project;
            }
        }
        return null;
    };

    self.updateProject = function (projectData) {
        var foundProject = self.findProject(projectData.path);
        if (foundProject) {
            foundProject.load(projectData);
        } else {
            self.projects.push(new ProjectModel(projectData))
        }
    };

    self.queryProjects = function () {
        API.project.list(function (data) {
            $(data['projects']).each(function (i, obj) {
                self.updateProject(obj);
            });
            if (self.files().length == 0) {
                self.selectProject(self.currentProject());
            }
        });
    };

    self.selectProject = function (project) {
        API.project.setCurrent(project.path(), function (data) {
            self.currentProject(project);
            self.queryFileList(project.path());
            self.queryMuteList();

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

    self.askRemoveProject = function (project) {
        if (confirm('是否确认【删除】该项目?')) {
            self.removeProject(project);
        }
    };

    self.removeProject = function (project) {
        API.project.remove(project.path(), function (data) {
            self.projects.remove(project);
        })
    };

    self.addProjectWithPath = function (path) {
        var $input = $("#new-path-input");
        var $btn = $('#project-add-btn');
        API.project.add(path, function (resp) {
            self.updateProject(resp.project);
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
        $input.val($.trim($input.val()));
        var projectPath = $input.val();
        if (projectPath) {
            self.addProjectWithPath(projectPath);
        } else {
            alert('请输入路径');
        }
        return false;
    };

    self.submitTargetHost = function (item, event) {
        var targetHost = $.trim($('#target-host-input').val());

        if (/^[\w\.]+$/.exec(targetHost)){
            API.project.setTargetHost(self.currentProject().path(), targetHost, function (resp) {
                self.currentProject().targetHost(targetHost);
            });
        } else {
            alert('请输入域名或ip地址（不带协议和路径）');
            $('#target-host-input').val(targetHost).focus().select();
        }
    };

    self.clearTargetHost = function (item, event) {
        self.currentProject().targetHost('');  // 这里很诡异，不能将input的内容清空
        $('#target-host-input').val('');
        API.project.setTargetHost(self.currentProject().path(), "", function (resp) {
            console.log(resp);
        });
    };

    // ================================= Files
    self.queryFileList = function (path) {
        self.files.removeAll();

        API.os.listDir(path, function (data) {
            self.files.removeAll();
            $(data['list']).each(function (i, obj) {
                var file = new FileModel(obj, self.currentProject());
                self.files.push(file);
            });
        });
    };

    self.refreshFolderSegments = function (path) {
        var rootPath = self.currentProject().path();
        var relPath = path.replace(rootPath, '');
        if (relPath[0] == '/') {
            relPath = relPath.substr(1);
        }
        var currentPath = rootPath;

        self.folderSegments.removeAll();
        $(relPath.split('/')).each(function (i, segment) {
            if (currentPath[currentPath.length - 1] != '/') {
                currentPath += '/';
            }
            currentPath += segment;
            if (segment) {
                self.folderSegments.push(new FolderSegment(segment, currentPath));
            }
        });
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

    // ========================== mutePath
    self.queryMuteList = function () {
        API.project.muteList(self.currentProject().path(), function (data) {
            self.currentProject().muteList(data['muteList']);
        });
    };

    self.toggleMute = function (file, event) {
        API.project.toggleMutePath(self.currentProject().path(), file.absolutePath(), file.isMute(), function (data) {
            self.queryMuteList();
        });
    };

    // =================================== misc
    self.showScriptHint = function() {
        $('#script-hint-link').css('visibility', 'hidden');
        $('#script-hint').show();
        $.cookie('show-script-hint', true);
    };

    self.hideScriptHint = function() {
        $('#script-hint-link').css('visibility', 'visible');
        $('#script-hint').hide();
        $.cookie('show-script-hint', false);
    };
}

var vm = new ViewModel();
ko.applyBindings(vm);

$(function () {
    vm.queryProjects();
});