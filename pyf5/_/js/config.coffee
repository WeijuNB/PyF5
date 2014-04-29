requirejs.config
    baseUrl: '/_/js'

    paths:
        underscore: 'libs/underscore-min'
        angular: 'libs/angular'
        ngRoute: 'libs/angular-route'
        'mgcrea.ngStrap': 'libs/angular-strap.tpl'

    shim:
        underscore:
            exports: '_'
        angular:
            exports: 'angular'
        ngRoute:
            deps: ['angular']
        'mgcrea.ngStrap':
            deps: ['angular', 'libs/angular-strap']
        'libs/angular-strap':
            deps: ['angular']