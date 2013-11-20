(function(){
                window.THEWEBSOCKET = new WebSocket("ws://localhost:8001");
                window.THEWEBSOCKET.onopen = function () {console.log("we in here") };
                var h = document.getElementsByTagName('h1')[0];
                window.THEWEBSOCKET.onmessage = function () {h.innerHTML = message};
                document.onclick = function () { window.THEWEBSOCKET.send('o hai there') };
          }())