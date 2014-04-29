// Generated by CoffeeScript 1.7.1
(function() {
  var libs;

  libs = ['angular', '../app', 'services/api'];

  define(libs, function(angular, app) {
    var IndexController;
    IndexController = function($rootScope, $scope, api) {
      $rootScope.projects = [];
      $rootScope.currentProject = null;
      $rootScope.listProjects = function() {
        return api.project.list().then(function(resp) {
          if (resp.status === 200 && !resp.data.error) {
            return $rootScope.projects = resp.data.projects;
          }
        });
      };
      return $rootScope.listProjects();
    };
    return app.controller('IndexController', IndexController);
  });

}).call(this);
