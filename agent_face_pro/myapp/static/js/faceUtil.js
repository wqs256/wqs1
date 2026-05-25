var faceUtile ={
      width:440,
      height:330,
      isOpen:false,
      promise:null,
      openVideo:  function (id) {
          var mythis = this;
          $("#"+id+"").empty();
          let videoComp = "<video id='myVideo' width='"+this.width+"' height='"+this.height+"' autoplay='autoplay' style='width: 100%; max-width: "+this.width+"px; height: auto; border-radius: 12px;'></video>" +
              "<canvas id='myCanvas' width='"+this.width+"' height='"+this.height+"' style='display: none'></canvas>";
          $("#"+id+"").append(videoComp);
          let constraints = {
              video: {width: mythis.width, height: mythis.height},
              audio: false
          };
          let video = document.getElementById("myVideo");

          if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
              alert("您的浏览器不支持摄像头功能");
              return;
          }

          this.promise = navigator.mediaDevices.getUserMedia(constraints);
          this.promise.then(function (MediaStream) {
              video.srcObject = MediaStream;
              video.play();
              mythis.isOpen = true;
          }).catch(function (err) {
              console.error("摄像头开启失败:", err);
              if (err.name === 'NotAllowedError') {
                  alert("摄像头权限被拒绝，请在浏览器设置中允许访问摄像头");
              } else if (err.name === 'NotFoundError') {
                  alert("未找到摄像头设备");
              } else {
                  alert("摄像头开启失败: " + err.message);
              }
              mythis.isOpen = false;
          });
      },

    getDecode:function () {
          if(this.isOpen){
              let myVideo = document.getElementById("myVideo");
              let myCanvas = document.getElementById("myCanvas");
              let ctx = myCanvas.getContext('2d');
              ctx.drawImage(myVideo, 0, 0, this.width, this.height);
              var decode = myCanvas.toDataURL();
              return decode;
          }else{
              alert("没有开启摄像头");
              return null;
          }
    }
}


