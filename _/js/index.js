
function queryAPI(cmd, params, callback) {
    var url = '/_/api?';
    var callback_name = '_jsonp_callback_' + parseInt(Math.random() * 100000000000);
    var param_pairs = ['cmd=' + cmd, 'callback=' + callback_name];

    for (var key in params) {
        param_pairs.push(key + '=' + params[key]);
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


function ProjectViewModel() {
    var self = this;

    self.path = ko.observable("");

    self.onSubmit = function(formElement) {
        queryAPI('setPath', {'path':self.path()}, function(data) {
            alert('已将没记录设置为：'+ self.path());
        });

        return false;
    }
}

var projectViewModel = new ProjectViewModel();

ko.applyBindings(projectViewModel);

$(function(){
    queryAPI('getPath', {}, function(data) {
        projectViewModel.path(data['path']);
    });
});