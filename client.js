// TODO -- fix this so it dynamically knows which IP address / port I'm using

(function(){
                window.THEWEBSOCKET = new WebSocket("ws://blagdons-macbook-air-2.local:8001");
                window.THEWEBSOCKET.onopen = function () {console.log("we in here") };
                window.THEWEBSOCKET.onmessage = function (message) {
                    var h = document.getElementsByTagName('h1')[0];
                    h.innerHTML = message.data};
                document.onclick = function () { window.THEWEBSOCKET.send('o hai there') };
          }())