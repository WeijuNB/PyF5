libs = ['angular', '../app']
define libs, (angular, app) ->

    api = ($http) ->
        API_URL = '/_/api/'

        query = (cmd, params={}) ->
            return $http.get(API_URL + cmd, params:params)

        return {
            os:
                f5Version: ->
                    query 'os/f5Version'
                listDir: (path) ->
                    query 'os/listDir', path:path
                writeFile: (path, content) ->
                    query 'os/writeFile', path:path, content:content
                localHosts: ->
                    query 'os/localHosts'
            project:
                list: ->
                    query 'project/list'
                add: (projectPath) ->
                    query 'project/add', path:projectPath
                remove: (projectPath) ->
                    query 'project/remove', path:projectPath
                update: (projectPath, options) ->
                    query 'project/update', path:projectPath, options:options
        }

    app.factory 'api', api

