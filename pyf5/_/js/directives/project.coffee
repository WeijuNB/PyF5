libs = ['angular', '../app', 'services/api']
define libs, (angular, app) ->

    project = (api) ->
        restrict: 'E'
        scope:
            model: '='
        replace: true
        templateUrl: '/_/views/_project.html'
        link: (scope, elem, attrs) ->
            scope.select = ->
                api.project.select(scope.model.path).then (data) ->
                    scope.$root.loadProjects()

            scope.remove = ($event) ->
                api.project.remove(scope.model.path).then ->
                    scope.$root.loadProjects()
                $event.stopPropagation()
                $event.preventDefault()


    app.directive 'project', project

