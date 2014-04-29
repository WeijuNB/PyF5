libs = ['angular', '../app', 'services/api']
define libs, (angular, app) ->

    IndexController = ($rootScope, $scope, api) ->
        $rootScope.projects = []

        $rootScope.currentProject = null

        $rootScope.listProjects = ->
            api.project.list().then (resp) ->
                if resp.status == 200 and not resp.data.error
                    $rootScope.projects = resp.data.projects

        $rootScope.listProjects()



    app.controller 'IndexController', IndexController

