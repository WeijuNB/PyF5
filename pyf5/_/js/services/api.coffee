libs = ['angular', '../app']
define libs, (angular, app) ->

    api = ($http, $q, $log) ->
        API_URL = '/_/api/'

        query = (cmd, params={}) ->
            deferred = $q.defer()
            $http.post(API_URL + cmd, params).then (resp) ->
                if resp.status != 200
                    $log.error cmd, params, '->', resp
                    deferred.reject("HTTP ERROR: #{resp.status}")
                    alert "HTTP ERROR: #{resp.status}"
                else if resp.data.error
                    $log.error cmd, params, '->', resp
                    deferred.reject(resp.data.error)
                    alert resp.data.error
                else
                    deferred.resolve(resp.data)
            , (resp) ->
                $log.error cmd, params, '->', resp
                deferred.reject("HTTP ERROR: #{resp.status}")
                alert "HTTP ERROR: #{resp.status}"
            return deferred.promise

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
                select: (projectPath) ->
                    query 'project/select', path:projectPath
                remove: (projectPath) ->
                    query 'project/remove', path:projectPath
                update: (projectPath, options) ->
                    query 'project/update', path:projectPath, options:options
        }

    app.factory 'api', api

