libs = ['angular', '../app', 'services/api']
define libs, (angular, app) ->

    IndexController = ($rootScope, $scope, api) ->
        $rootScope.projects = []

        $rootScope.loadProjects = ->
            api.project.list().then (data) ->
                $rootScope.projects = data

        $scope.newProject = path:''
        $scope.addProject = (path) ->
            api.project.add(path).then ->
                $scope.newProject.path = ''
                $rootScope.loadProjects()

        $rootScope.loadProjects()



    app.controller 'IndexController', IndexController

