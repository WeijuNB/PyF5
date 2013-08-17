postAPI = (cmd, params, success_handler, error_handler) ->
    url = "/_/api/#{cmd}"
    $.post(url, params
        (resp) ->
            if resp.status == 'error'
                if error_handler
                    error_handler resp
                else
                    alert resp.message
            else
                success_handler(resp) if success_handler
        'json'
    ).fail (resp) ->
        console.log '调用失败', params, resp


window.API =
    project:
        list: (sh, eh) -> # successHandler, errorHandler
            postAPI 'project/list', {}, sh, eh
        add: (projectPath, sh, eh) ->
            postAPI 'project/add', {path: projectPath}, sh, eh
        remove: (projectPath, sh, eh) ->
            postAPI 'project/remove', {path: projectPath}, sh, eh
        update: (project, sh, eh) ->
            projectData = project.export()
            postAPI 'project/update', {project: JSON.stringify projectData}, sh, eh

    os:
        f5Version: (sh, eh) ->
            postAPI 'os/f5Version', {}, sh, eh
        listDir: (path, sh, eh) ->
            postAPI 'os/listDir', {path: path}, sh, eh
        writeFile: (path, content, sh, eh) ->
            postAPI 'os/writeFile', {path: path, content: content}, sh, eh
        localHosts: (sh, eh) ->
            postAPI 'os/localHosts', {}, sh, eh