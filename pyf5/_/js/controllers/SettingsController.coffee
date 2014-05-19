libs = ['angular', '../app', 'services/api']
define libs, (angular, app) ->

    SettingsController = ($log, $rootScope, $scope, api, $location) ->
        $scope.project = null
        $scope.f5Port = $location.port
        $rootScope.$watch 'projects', (projects) ->
            for project in projects
                if project.active
                    return $scope.project = project
            return $scope.project = null

        $scope.model = {
            delayOption: null
        }

        $scope.delayOptions = [
            {name: '延迟 1 秒', value: 1}
            {name: '延迟 2 秒', value: 2}
            {name: '延迟 3 秒', value: 3}
            {name: '延迟 5 秒', value: 5}
            {name: '延迟 7 秒', value: 7}
            {name: '延迟 10 秒', value: 10}
            {name: '延迟 15 秒', value: 15}
        ]

        $scope.hoveringMode = null
        $scope.setHoveringMode = (mode) ->
            $scope.hoveringMode = mode

        $scope.promptHostPort = ->
            host_port = prompt '请输入目标服务器名和端口，以":"分割\n（例 "localhost:8080")'
            return if host_port == null
            [host, port] = host_port.split(':')
            $scope.project.host = host
            $scope.project.port = parseInt port
            api.project.update($scope.project.path, $scope.project)
            return true

        $scope.switchMode = (mode) ->
            return if mode == $scope.model.mode
            if mode == 'dynamic'
                if not $scope.project.host
                    if $scope.promptHostPort()
                        $scope.project.mode = mode
                else
                    $scope.project.mode = mode
                api.project.update($scope.project.path, $scope.project)
            else
                $scope.project.mode = mode
                api.project.update($scope.project.path, $scope.project)

        $scope.$watch 'model.delayOption', (newValue) ->
            console.log 'model.delayOption', newValue


    app.controller 'SettingsController', SettingsController

