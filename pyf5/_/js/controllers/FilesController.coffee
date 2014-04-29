libs = ['angular', '../app', 'services/api']
define libs, (angular, app) ->

    FilesController = ($log, $rootScope, $scope, api) ->
        $scope.rootPath = ''
        $scope.relativePath = ''

        $scope.levels = []
        $scope.list = []

        $scope.queryList = () ->
            path = [$scope.rootPath, $scope.relativePath].join('/')
            if path
                api.fs.list(path).then (data) ->
                    $scope.list = data

        $scope.setRootPath = (path) ->
            $log.debug 'rootPath', path
            return if path == $scope.rootPath

            $scope.rootPath = path
            $scope.setRelativePath('')
            $scope.list = []
            $scope.queryList()


        $scope.setRelativePath = (path) ->
            $scope.relativePath = path
            $scope.levels = []

            names = []
            for name in path.split('/')
                continue if not name
                names.push name
                level = {
                    name: name
                    relativePath: names.join('/')
                }

                $scope.levels.push level

            $scope.queryList()

        $scope.click = (item) ->
            if item.type == 'DIR'
                $scope.setRelativePath([$scope.relativePath, item.name].join('/'))
            else
                window.open("#{$scope.relativePath}/#{item.name}", '_blank')


        $rootScope.$watch 'projects', (newValue, oldValue) ->
            if not newValue or newValue.length == 0
                $scope.setRootPath("")

            for project in newValue
                if project.active
                    $scope.setRootPath(project.path)
                    break
        , true



    app.controller 'FilesController', FilesController

