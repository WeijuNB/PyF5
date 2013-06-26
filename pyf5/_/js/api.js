function queryAPIScript(cmd, params, success_handler, error_handler) {
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

function postAPIRequest(cmd, params, success_handler, error_handler) {
    var url = '/_/api?cmd=' + cmd;
    $.post(url, params, function (data) {
        if (data['status'] == 'ok') {
            success_handler(data);
        } else {
            if (error_handler) {
                error_handler(data);
            } else {
                alert(data['message']);
            }
        }
    }, 'json');
}

var API = {
    project: {
        list: function(successHandler, errorHandler) {
            queryAPIScript('project.list', {}, successHandler, errorHandler);
        },
        setCurrent: function(projectPath, successHandler, errorHandler) {
            queryAPIScript('project.setCurrent', {path:projectPath}, successHandler, errorHandler);
        },
        add: function(projectPath, successHandler, errorHandler) {
            queryAPIScript('project.add', {path:projectPath}, successHandler, errorHandler);
        },
        remove: function(projectPath, successHandler, errorHandler) {
            queryAPIScript('project.remove', {path:projectPath}, successHandler, errorHandler);
        },
        blockPaths: function(projectPath, successHandler, errorHandler) {
            queryAPIScript('project.blockPaths', {projectPath: projectPath}, successHandler, errorHandler);
        },
        toggleBlockPath: function(projectPath, filePath, block, successHandler, errorHandler) {
            queryAPIScript('project.toggleBlockPath', {
                projectPath: projectPath,
                blockPath: filePath,
                action: block ? 'off' : 'on'
            }, successHandler, errorHandler);
        }

    },
    os: {
        listDir: function(path, successHandler, errorHandler) {
            queryAPIScript('os.listDir', {path: path}, successHandler, errorHandler);
        },
        writeFile: function(path, content, successHandler, errorHandler) {
            postAPIRequest('os.writeFile', {path: path, content:content}, successHandler, errorHandler)
        }
    }
};