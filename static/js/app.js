angular.module('network-analyse', ['ngResource', 'ngRoute', 'ngCookies'])
  .config(['$routeProvider', function ($routeProvider) {
          $routeProvider
            .when('/', {
                templateUrl: 'static/views/home/home.html', 
                controller: 'HomeController'})
            .when('/diy', {
                templateUrl: 'static/views/home/diy.html', 
                controller: 'DiyController'})
            .otherwise({redirectTo: '/'});
    }]);

angular.module('network-analyse').controller('NavbarCtrl', ['$rootScope', '$scope', '$cookies',
   function($rootScope, $scope, $cookies) {
       $rootScope.page = 1;
       $scope.setPage = function(num) {
         $rootScope.page = num;
       };
       $scope.isPage = function(num) {
           return $scope.page === num;
       };
       var sessionID = $cookies.get('sessionID');
       if (!sessionID) {
           sessionID = new Date().getTime();
           $cookies.put('sessionID', sessionID);
       };
       $scope.sid = sessionID;
       $rootScope.sid = sessionID;
   }
]);

