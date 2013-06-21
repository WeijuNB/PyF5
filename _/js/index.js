
function queryAPI(cmd, params, callback) {
    var url = '/_/api?';
    var callback_name = '_jsonp_callback_' + parseInt(Math.random() * 100000000000);
    var param_pairs = ['cmd=' + cmd, 'callback=' + callback_name];

    for (var key in params) {
        param_pairs.push(key + '=' + encodeURIComponent(params[key]));
    }
    url += param_pairs.join('&');

    window[callback_name] = function(data) {
        delete window[callback_name];
        callback(data);
    };
    $.getScript(url)
        .fail(function(){
            if (window[callback_name]) {
                delete window[callback_name];
            }
        });
}


function ProjectViewModel(path) {
    var self = this;

    self.path = ko.observable(path);
}

function ProjectsViewModel() {
    var self = this;

    self.projects = ko.observableArray([]);
    self.currentProject = ko.observable(null);

    self.selectProject = function(project) {
        queryAPI('setPath', {path:project.path()}, function(data) {
            if (data.status == 'ok'){
                self.currentProject(project);
            } else {
                alert(data.message);
            }
        })
    };

    self.selectProjectWithPath = function(path) {
        var project;
        for (var i in self.projects()) {
            project = self.projects[i]
            if (project.path() == path) {
                self.selectProject(project)
                break;
            }
        }
    };

    self.updateProjectsWithPaths = function(paths) {
        self.projects.removeAll();
        $(paths).each(function(i, path) {
            self.projects.push(new ProjectViewModel(path));
        });
    };

    self.onSubmit = function(formElement) {
        var new_path = $("#new-path-input").val();
        if (new_path) {
            queryAPI('addPath', {path:new_path}, function(data) {
                if (data.status == 'ok') {
                    self.updateProjectsWithPaths(data['paths']);
                } else {
                    alert(data.message);
                }
            });
        }
        return false;
    };
}

var projectsViewModel = new ProjectsViewModel();

ko.applyBindings(projectsViewModel);

$(function(){
    queryAPI('getPaths', {}, function(data) {
        if (data.status == 'ok') {
            projectsViewModel.updateProjectsWithPaths(data['paths'])
        }
        queryAPI('getPath', {}, function(data) {
            if (data.status == 'ok') {
                projectsViewModel.selectProjectWithPath(data.path);
            }
        });
    });
});