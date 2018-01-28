angular.module('network-analyse')
.controller('DiyController', ['$scope', '$http', '$rootScope', function ($scope, $http, $rootScope) {
    $scope.timeStamp = new Date().getTime();
    $rootScope.page = 2;
    var can = document.getElementById('cav');
    var ctx = can.getContext("2d");
    var x = 0, y = 0;
    var color = '#FF0000';
    $scope.lineWidth = 15;
    $scope.draw_model = "line"; 
    var MAX_SIZE = 400;

    // 清空
    $scope.clear_all = function() {
        ctx.clearRect(0, 0, can.width, can.height);
    };

    // 画笔 
    var draw = function(event) {
        var nx = event.offsetX;
        var ny = event.offsetY;
        ctx.lineTo(x,y);
        ctx.stroke();
        x = nx;
        y = ny;
    };
    // 橡皮
    var earse = function(event) {
        var nx = event.offsetX;
        var ny = event.offsetY;
        ctx.clearRect(x, y, $scope.lineWidth, $scope.lineWidth);
        x = nx;
        y = ny;
    }
    // 这里没有使用jquery, 第三个参数false: 在事件冒泡阶段触发
    can.addEventListener("mousedown", function(e){
        ctx.strokeStyle = color;
        ctx.lineWidth = $scope.lineWidth;
        e.preventDefault();
        x = e.offsetX;
        y = e.offsetY;
        ctx.beginPath();
        ctx.moveTo(x,y);
        if($scope.draw_model === "line") {
            can.addEventListener("mousemove", draw, false);
        } else {
            ctx.clearRect(x, y, $scope.lineWidth, $scope.lineWidth);
            can.addEventListener("mousemove", earse, false);
        }
    }, false);
    can.addEventListener("mouseup", function(e){
        if($scope.draw_model === "line") {
            can.removeEventListener("mousemove", draw, false);
        } else {
            can.removeEventListener("mousemove", earse, false);
        }
    }, false);
    can.style.cursor = "crosshair";
   
    // slide bar
    // 支持鼠标滚轮修改画笔大小
    var lw = document.getElementById('lineWidth');
    lw.addEventListener("mousewheel", function(e) {
       if (e.deltaY>0 && $scope.lineWidth < 50) {
           $scope.lineWidth = $scope.lineWidth + 1;
       } else if (e.deltaY<0 && $scope.lineWidth >= 1) {
           $scope.lineWidth = $scope.lineWidth - 1;
       }
       $scope.$apply();
    }, false);
    
    //var sbarX = 0.33;
    //var sbarData = Math.round(sbarX*100) + '%';
    //$scope.sbarPos = {left: sbarData};
    //var sbar = document.getElementById('sbar');
    //var sbarHandle = document.getElementById('sbar-handle');
    //var drag_sbar_handle = function(event) {
        //var nx = event.offsetX;
    //};
    //sbar_handle.addEventListener("mousedown", function(e){
        //sbar_handle.addEventListener("mousemove", drag_sbar_handle, false);
    //});
    //sbar-handle.addEventListener("mouseup", function(e){
        //x = e.offsetX;
    //});

   // canvas的背景
   $scope.bg_style = {
        "background": "white",
   };

   // 弹窗 0: 无弹窗， 1: 上传图片
   $scope.modalNum = 0;
   $scope.setModal = function(num) {
     $scope.modalNum = num;
   };
   $scope.isSetModal = function(num) {
       return $scope.modalNum === num;
   };
   // 图片上传
   var fileInput = document.getElementById('upload_file');
   var can_preview = document.getElementById('can_preview');
   var ctx_preview = can_preview.getContext("2d");
   var reader = new FileReader();
   var image = new Image();
   reader.onload = function(e) {
       image.onload=function(){
           // 用canvas来压缩图片, 等比例缩放，最长边不超过MAX_SIZE
           var w = image.naturalWidth,
               h = image.naturalHeight;
           var max_size = Math.max(w, h);
           if (max_size > MAX_SIZE) {
               if (w > h) {
                  h = h / w * MAX_SIZE;
                  w = MAX_SIZE;
               } else {
                  w = w / h * MAX_SIZE;
                  h = MAX_SIZE;
               }
           }
           can_preview.width = w;
           can_preview.height = h;
           ctx_preview.drawImage(image, 0, 0,image.naturalWidth, image.naturalHeight, 0, 0, w, h); 
       };
       image.src = e.target.result;
   };
   // 监听选择图片，压缩和预览
   fileInput.addEventListener('change', function(){
       if (fileInput.value) {
           var file = fileInput.files[0];
           reader.readAsDataURL(file);
       }
   });
   $scope.chooseImg = function() {
       can.width = can_preview.width
       can.height = can_preview.height
       $scope.bg_style = {
          "background-image": "url(" + can_preview.toDataURL() + ")",
       };
       $scope.setModal(0);
   };
   $scope.diy_input_src = "";
   $scope.diy_g_output_src = "";
   $scope.diy_origin_src = "";

   $scope.sendImg = function() {
      var fd = new FormData();
      fd.append('sid', $rootScope.sid);
      var origin_fname = "userImg_" + $rootScope.sid +".jpeg"
      var mask_fname = "userMask_" + $rootScope.sid +".jpeg"
      var origin_f, mask_f;
      var counter = 0;
      function try_send_query() {
         if (counter == 2) { 
           $http.post("/api/inpaint_diy", fd, {
              headers: {'Content-Type': undefined},
              transformRequest: angular.identity,
           }).then(function successCallback(resp) { 
               if (resp.data.success === 0) {
                   $scope.timeStamp = new Date().getTime();
                   $scope.diy_input_src = resp.data.input_url + "?" + $scope.timeStamp;
                   $scope.diy_g_output_src = resp.data.g_output_url + "?" + $scope.timeStamp;
                   $scope.diy_q_output_src = resp.data.q_output_url + "?" + $scope.timeStamp;
                   $scope.diy_origin_src = can_preview.toDataURL();
                   $scope.setModal(2);
               } else {
                   alert(resp.data);
               }
           });
         }
     }
      if (fileInput.value) {
         origin_fname = fileInput.files[0].name;
          can_preview.toBlob(function(b){
              fd.append('origin_f', new File([b], origin_fname));
              counter = counter + 1;
              try_send_query();
          }, "image/jpeg");
          can.toBlob(function(b){
              fd.append('mask_f', new File([b], mask_fname));
              counter = counter + 1;
              try_send_query();
          }, "image/png");
      }
   };
}]);

