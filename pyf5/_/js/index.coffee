libs = [ 'underscore', 'angular',
    'ngRoute',
    'mgcrea.ngStrap'

    'services/api',

    'controllers/IndexController',
    'controllers/FilesController',
    'controllers/SettingsController',

    'directives/project'
]
main = (_, angular) ->
    index = angular.module 'index', ['ngRoute', 'mgcrea.ngStrap', 'app']

    angular.element(document).ready ->
        angular.bootstrap(document, ['index'])


require ['/_/js/config.js'], ->
    require libs, main