function joinPath(p1, p2) {
    var path = [p1 , p2].join('/');
    path = path.replace(/\/+/g, '/');
    return path;
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

    self.mute = function () {
        if (project.muteList.indexOf(self.relativePath()) == -1) {
            project.muteList.push(self.relativePath());
            project.save();
        }
    };

    self.unmute = function () {
        if (project.muteList.indexOf(self.relativePath()) != -1) {
            project.muteList.remove(self.relativePath());
            project.save();
        }
    };

    self.onClick = function () {
        if (self.type() == 'DIR') {
            project.currentFolder(self.relativePath());
            return false;
        }
        return true;
    }
}


function FolderSegment(name, relativePath, project) {
    var self = this;

    self.name = ko.observable(name);
    self.relativePath = ko.observable(relativePath);

    self.onClick = function () {
        project.currentFolder(self.relativePath());
    };
}


function ProjectModel(data, root) {
    var self = this;
    self.root = root;

    // 和服务器对应的数据结构-----------------------------------------
    self.path = ko.observable("");
    self.active = ko.observable(false);
    self.muteList = ko.observableArray([]);
    self.targetHost = ko.observable('');
    self.domains = ko.observableArray([]);
    self.activeDomain = ko.observable('127.0.0.1');

    // 域名切换相关--------------------------------------------------
    self.activeDomains = ko.observableArray(['127.0.0.1']);
    self.activeDomains.subscribe(function (newValue) {
        self.activeDomain(newValue[0]);
        setTimeout(self.save, 100); // 这里的save会和其他save冲突，导致后发先至引起数据错乱，所以暂时丑陋地解决一下
        self.QRCodeFile(self.QRCodeFile());
    });
    self.allHosts = ko.computed(function () {
        return self.domains().concat(root.localHosts());
    });
    self.activeDomainAndPort = ko.computed(function () {
        if (root.port()) {
            return self.activeDomain() + ':' + root.port();
        } else {
            return self.activeDomain();
        }
    });
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

    // settings ---------------------------------------------
    self.showSettings = ko.observable($.cookie('hideSettings')!='true');
    self.showSettings.subscribe(function (newValue) {
        $.cookie('hideSettings', !newValue);
    });
    self.submitTargetHost = function (item, event) {
        var targetHost = $.trim($('#target-host-input').val());

        if (!targetHost) {
            self.clearTargetHost();
        } else if (/^[\w\.:\-]+$/.exec(targetHost)){
            self.targetHost(targetHost);
            self.save()
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
        self.targetHost('');  // 这里很诡异，不能将input的内容清空
        $('#target-host-input').val('');
        self.save();
    };

    // file management -------------------------------------
    self.files = ko.observableArray([]);
    self.folderSegments = ko.observableArray([]);
    self.currentFolder = ko.observable('');
    self.currentFolder.subscribe(function (relativePath) {
        self.folderSegments.removeAll();
        var parts = relativePath.split('/');
        var relativeParts = [];
        $(parts).each(function (i, part) {
            relativeParts.push(part);
            if (part) {
                self.folderSegments.push(new FolderSegment(part, relativeParts.join('/'), self));
            }
        });
        self.queryFileList(joinPath(self.path(), relativePath));
    });
    self.currentFolder.extend({notify:'always'}); // 不论是否有修改，都发生subscribe
    self.goRoot = function () {
        self.currentFolder('');
    };

    self.queryFileList = function (path) {
        self.files.removeAll();

        API.os.listDir(path, function (data) {
            self.files.removeAll();
            $(data['list']).each(function (i, obj) {
                var file = new FileModel(obj, self);
                self.files.push(file);
            });
            $('#file-list td.op a').tooltip();
        });
    };

    // QRCode --------------------------------------------
    self.QRCodeFile = ko.observable(null);
    self.QRCodeFile.extend({notify:'always'});
    self.QRCodeFile.subscribe(function (newValue) {
        if (newValue) {
            $('#qrcode-modal').modal()
                .on('hidden', function () {
                    self.QRCodeFile(null);
                });
            self.updateQRCode(newValue.url());
        }
    });


    self.QRUrlChange = function (item, event) {
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

    self.showQRCode = function (item, event) {
        self.QRCodeFile(item);
    };

    // save/load/export ----------------------------------
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

    if (data) {
        self.load(data);
    }
}


function ViewModel() {
    var self = this;

    self.port = ko.observable(location.port);
    self.localHosts = ko.observableArray(['127.0.0.1']);

    self.projects = ko.observableArray([]);
    self.projects.subscribe(function (newValue) {
        setTimeout(function () {
            $('#projects .op a').tooltip();
        }, 500);
    });

    self.activeProject = ko.observable(null);
    self.activeProject.subscribe(function (project) {
        if (project) {
            if (!project.active()) {
                project.active(true);
                console.log('active save');
                project.save();
            }
            if (project.files().length == 0) {
                project.currentFolder('');
            }
        }
        $(self.projects()).each(function (i, item) {
            if (item && item != project) {
                if (item.active()) {
                    item.active(false);
                    item.save();
                }
            }
        });

        setTimeout(function () {
            $('#project [data-toggle=tooltip]').tooltip();
        }, 500);
    });

    self.queryLocalHosts = function () {
        API.os.localHosts(function (resp) {
            self.localHosts(resp.hosts);
        });
    };

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
        var project = self.findProject(projectData.path);
        if (project) {
            project.load(projectData);
        } else {
            project = new ProjectModel(projectData, self);
            self.projects.push(project)
        }
        return project;
    };

    self.queryProjects = function () {
        API.project.list(function (data) {
            $(data['projects']).each(function (i, obj) {
                var project = self.loadProjectData(obj);
                if (project.active() && project != self.activeProject()) {
                    self.activeProject(project);
                }
            });
        });
    };

    self.removeProject = function (project) {
        self.projects.remove(project);
        API.project.remove(project.path());
        if (self.activeProject() == project) {
            self.activeProject(null);
        }
    };

    self.addProjectWithPath = function (path) {
        API.project.add(path, function (resp) {
            self.loadProjectData(resp.project);
            if (self.projects().length == 1 && !self.activeProject()) {
                self.activeProject(self.projects()[0])
            }
            $("#new-path-input").val('');
        });
    };

    self.onSelectProject = function (project) {
        self.activeProject(project);
    };

    self.askRemoveProject = function (project) {
        if (confirm('是否确认【删除】该项目?')) {
            self.removeProject(project);
        }
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

    self.queryLocalHosts();
    self.queryProjects();
}

var vm = new ViewModel();

$(function () {
    ko.applyBindings(vm);

    $.getScript('http://www.getf5.com/update.js');

    (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
        (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
        m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
    })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

    ga('create', 'UA-22253493-9', '127.0.0.1');
    ga('send', 'pageview');
});