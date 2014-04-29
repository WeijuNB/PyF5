libs = ['angular', '../app', 'services/api']
define libs, (angular, app) ->

    project = (api) ->
        restrict: 'E'
        scope:
            model: '='
        replace: true
        templateUrl: '/_/views/_project.html'
        link: (scope, elem, attrs) ->
            console.log 'fuck', scope

            scope.isActive = ->
                return scope.$root.currentProject?.path == scope.model.path

            scope.select = ->
                scope.$root.currentProject = scope.model

            scope.remove = ($event) ->
                console.log api
                api.project.remove(scope.model.path).then ->
                    scope.$root.listProjects()
                $event.preventDefault()
                $event.stopPropagation()


    app.directive 'project', project

