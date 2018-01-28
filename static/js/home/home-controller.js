angular.module('network-analyse')
.controller('HomeController', ['$scope', '$http', '$rootScope', 
 function ($scope, $http, $rootScope) {
   $rootScope.page = 1;
   $scope.job = 2;
   $scope.timeStamp = new Date().getTime();
   $scope.tab = 1;
   $scope.setTab = function(newTab) {
       $scope.tab = newTab;
       // 第一次翻tab时，需要手动运行一次inpainting
       if (! $scope.mask_src) {
           refresh_inpainting("1");
       };
   };
   $scope.isSet = function(tabNum) {
       return $scope.tab === tabNum;
   };


   send_query = function(url, data) {
        return $http({
                      method : 'GET',
                      url : url,
              }).then(function successCallback(resp){
                      return resp;
              });
   };
   refresh_inpainting = function(refresh_mask) {
       var inpaint_url = "api/inpaint/";
       if ($scope.tab === 1) {
           inpaint_url = "api/inpaint_small/";
       }
       send_query(inpaint_url + $scope.job + 
            "?sid=" + $rootScope.sid + 
            "&refresh_mask=" + refresh_mask
       ).then(function(resp){
           $scope.timeStamp = new Date().getTime();
           if ($scope.tab === 2) {
               $scope.mask_src = resp.data.mask_url + "?" + $scope.timeStamp;
               $scope.input_src = resp.data.input_url + "?" + $scope.timeStamp;
               $scope.g_output_src = resp.data.g_output_url + "?" + $scope.timeStamp;
               $scope.q_output_src = resp.data.q_output_url + "?" + $scope.timeStamp;
               $scope.origin_src = resp.data.origin_url + "?" + $scope.timeStamp;
           } else {
               $scope.small_mask_src = resp.data.mask_url + "?" + $scope.timeStamp;
               $scope.small_input_src = resp.data.input_url + "?" + $scope.timeStamp;
               $scope.small_g_output_src = resp.data.g_output_url + "?" + $scope.timeStamp;
               $scope.small_q_output_src = resp.data.q_output_url + "?" + $scope.timeStamp;
               $scope.small_origin_src = resp.data.origin_url + "?" + $scope.timeStamp;
           }
       });
   };

   $scope.refresh_mask = function() {
       refresh_inpainting("1");
   }; 

   refresh_inpainting("1");

   $scope.next_img = function() {
     $scope.job = ($scope.job + 1) % 100;
     if ($scope.tab === 1) {
         // 128 * 128， 下翻图片时遮罩不改
         refresh_inpainting("0");
     } else {
         refresh_inpainting("1");
     }
   }; 
   $scope.previous_img = function() {
     $scope.job = ($scope.job - 1) % 100;
     if ($scope.tab === 1) {
         // 128 * 128， 下翻图片时遮罩不改
         refresh_inpainting("0");
     } else {
         refresh_inpainting("1");
     }
   }; 

}]);
