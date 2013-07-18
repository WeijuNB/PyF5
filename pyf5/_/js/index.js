function joinPath(p1, p2) {
    var path = [p1 , p2].join('/');
    path = path.replace(/\/+/g, '/');
    return path;
}

function ProjectModel(data, root) {
    var self = this;

    self.root = root;

    self.path = ko.observable("");
    self.active = ko.observable(false);
    self.muteList = ko.observableArray([]);
    self.targetHost = ko.observable('');
    self.domains = ko.observableArray([]);
    self.activeDomain = ko.observable('127.0.0.1');

    // 试了无数的其他方法，最后只能用这种官方的方法（options + selectedOptions）来实现了
    self.activeDomains = ko.observableArray(['127.0.0.1']);
    self.activeDomains.subscribe(function (newValue) {
        console.log(newValue);
        self.activeDomain(newValue[0]);
        self.save();
        self.root.QRCodeFile(self.root.QRCodeFile()); // todo: so ugly, refactor this
    });
    self.allHosts = ko.computed(function () {
        return self.domains().concat(root.localHosts());
    });

    self.load = function (data) {
        self.path(data.path);
        self.active(data && data.active ? data.active : false);
        self.muteList(data && data.muteList ? data.muteList : []);
        self.targetHost(data && data.targetHost ? data.targetHost : '');
        self.domains(data && data.domains ? data.domains : []);
        self.activeDomain(data && data.activeDomain ? data.activeDomain : '127.0.0.1');

        self.activeDomains([self.activeDomain()]);
    };

    self.save = function () {
        API.project.update(self);
    };

    self.export = function () {
        return {
            path: self.path(),
            active: self.active(),
            muteList: self.muteList(),
            targetHost: self.targetHost(),
            domains: self.domains(),
            activeDomain: self.activeDomain()
        };
    };

    self.clickAddDomain = function (item, event) {
        var domain = $.trim(prompt('请输入想要添加的域名：'));
        if (domain) {
            if (!/^[\w\.\-]+$/.exec(domain)) {
                alert('格式不对吧');
            } else {
                if (self.domains.indexOf(domain) > -1) {
                    alert('域名已存在'); // todo: 直接选择
                } else {
                    self.domains.unshift(domain);
                    self.activeDomains([domain]);
                }
            }
        }
    };

    self.clickRemoveDomain = function (item, event) {
        self.domains.remove(self.activeDomain());
        if (self.allHosts().length) {
            self.activeDomains([self.allHosts()[0]]);
        }
    };

    if (data) {
        self.load(data);
    }
}

function FolderSegment(name, relativePath) {
    var self = this;

    self.name = ko.observable(name);
    self.relativePath = ko.observable(relativePath);
}


function FileModel(data, project) {
    var self = this;

    self.name = ko.observable(data['name']);
    self.type = ko.observable(data['type']);
    self.absolutePath = ko.observable(data['absolutePath']);

    self.relativePath = ko.computed(function () {
        var relPath = self.absolutePath().replace(project.path(), '');
        if (relPath && relPath[0] == '/') {
            relPath = relPath.substr(1);
        }
        return relPath;
    });

    self.url = ko.computed(function () {
        var root = project.root;
        if (root.port()) {
            return 'http://' + project.activeDomain() + ':' + root.port() + '/' + self.relativePath();
        } else {
            return 'http://' + project.activeDomain() + '/' + self.relativePath();
        }
    });

    self.isMuted = ko.computed(function () {
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

function ViewModel() {
    var self = this;

    self.port = ko.observable(location.port);
    self.localHosts = ko.observableArray(['127.0.0.1']);
    self.activeHost = ko.observable('127.0.0.1');
    self.hostText = ko.computed(function () {
        if (self.port()) {
            return self.activeHost() + ':' + self.port();
        } else {
            return self.activeHost();
        }
    });

    self.showSettings = ko.observable(!$.cookie('hideSettings'));
    self.showSettings.subscribe(function (newValue) {
        $.cookie('hideSettings', newValue);
    });

    self.projects = ko.observableArray([]);
    self.projects.subscribe(function (newValue) {
        setTimeout(function () {
            $('#projects .op a').tooltip();
        }, 500);
    });

    self.activeProject = ko.computed({
        read: function () {
            var project;
            for (var i = 0; i < self.projects().length; i += 1) {
                project = self.projects()[i];
                if (project.active()) {
                    return project;
                }
            }
            return null;
        },
        write: function(activeProject) {
            var project;
            if (activeProject != self.activeProject()) {
                for (var i = 0; i < self.projects().length; i += 1) {
                    project = self.projects()[i];
                    if (project.path() != activeProject.path()) {
                        project.active(false);
                    } else {
                        project.active(true);
                        project.save()
                    }
                }
            }
        },
        owner: self
    });
    self.activeProject.subscribe(function (newValue) {
        setTimeout(function () {
            $('#project [data-toggle=tooltip]').tooltip();
        }, 500)
        self.currentFolder('');
    });

    self.folderSegments = ko.observableArray([]);
    self.currentFolder = ko.observable('');
    self.currentFolder.subscribe(function (relativePath) {
        self.folderSegments.removeAll();
        var parts = relativePath.split('/');
        var relativeParts = [];
        $(parts).each(function (i, part) {
            relativeParts.push(part);
            if (part) {
                self.folderSegments.push(new FolderSegment(part, relativeParts.join('/')));
            }
        });
        if (self.activeProject()) {
            self.queryFileList(joinPath(self.activeProject().path(), relativePath));
        }
    });
    self.currentFolder.extend({notify:'always'}); // 不论是否有修改，都发生subscribe

    self.files = ko.observableArray([]);
    self.QRCodeFile = ko.observable(null);
    self.QRCodeFile.subscribe(function (newValue) {
        if (newValue) {
            $('#qrcode-modal').modal()
                .on('hidden', function () {
                    self.QRCodeFile(null);
                });
            self.updateQRCode(newValue.url());
        }
    });
    self.QRCodeFile.extend({notify:'always'});

    self.QRUrlChange = function (item, event) {
        console.log($(event.target).val());
        self.updateQRCode($(event.target).val());
    };

    self.updateQRCode = function (text) {
        var $el = $('#qrcode');
        $el.empty();
        $el.qrcode({
            width: $el.width(),
            height: $el.height(),
            text: text
        });
    };

    self.hostChange = function (item, event) {
        console.log(item, event);
    };



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

    self.loadProjectData = function (projectData) {
        var foundProject = self.findProject(projectData.path);
        if (foundProject) {
            foundProject.load(projectData);
        } else {
            self.projects.push(new ProjectModel(projectData, self))
        }
    };

    self.queryProjects = function () {
        API.project.list(function (data) {
            $(data['projects']).each(function (i, obj) {
                self.loadProjectData(obj);
            });
            if (self.files().length == 0) {
                self.selectProject(self.activeProject());
            }
        });
    };

    self.selectProject = function (project) {
        self.activeProject(project);
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
        API.project.add(path, function (resp) {
            self.loadProjectData(resp.project);
            if (self.projects().length == 1 && !self.activeProject()) {
                self.selectProject(self.projects()[0]);
            }
            $("#new-path-input").val('');
        }, function (data) {
            alert(data['message']);
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
        var targetHost = $.trim($('#target-host-input').val()),
            project = self.activeProject();

        if (!targetHost) {
            self.clearTargetHost();
        } else if (/^[\w\.:\-]+$/.exec(targetHost)){
            project.targetHost(targetHost);
            project.save()
        } else {
            alert('请输入域名或ip地址（不带协议和路径）和端口，如：\n' +
                '127.0.0.1:8080\n' +
                '192.168.0.101\n' +
                'domain.com:8080\n' +
                'mysite.com');
            $('#target-host-input').val(targetHost).focus().select();
        }
    };

    self.clearTargetHost = function (item, event) {
        var project = self.activeProject();
        project.targetHost('');  // 这里很诡异，不能将input的内容清空
        project.save();
        $('#target-host-input').val('');
    };

    // ================================= Files
    self.queryFileList = function (path) {
        self.files.removeAll();

        API.os.listDir(path, function (data) {
            self.files.removeAll();
            $(data['list']).each(function (i, obj) {
                var file = new FileModel(obj, self.activeProject());
                self.files.push(file);
            });
            $('#file-list td.op a').tooltip();
        });
    };

    self.clickFile = function (file, event) {
        if (file.type() == 'DIR') {
            self.enterFolder(file.relativePath());
            return false;
        }
        return true;
    };

    self.clickFolderSegment = function (fs, event) {
        self.currentFolder(fs.relativePath());
    };

    self.enterFolder = function (relativePath) {
        self.currentFolder(relativePath);
    };

    self.toggleMute = function (file, event) {
        var project = self.activeProject(),
            mutePath = file.relativePath();

        if (file.isMuted()) {
            project.muteList.remove(mutePath);
        } else {
            if (project.muteList.indexOf(mutePath) == -1) {
                project.muteList.push(mutePath);
            }
        }
        project.save();
    };

    // ========================== misc
    self.queryLocalHosts = function () {
        API.os.localHosts(function (resp) {
            self.localHosts(resp.hosts);
        });
    };

    self.showQRCode = function (item, event) {
        self.QRCodeFile(item);
    };
}

var vm = new ViewModel();

$(function () {
    ko.applyBindings(vm);
    vm.queryLocalHosts();
    vm.queryProjects();

});