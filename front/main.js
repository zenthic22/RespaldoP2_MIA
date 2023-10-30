let url = "http://3.92.76.166/4000"
let lista_reportes = [];

function keyup(event){
  var numberOfLines = event.value.split("\n").length
  event.parentElement.getElementsByClassName("line-numbers")[0].innerHTML = Array(numberOfLines)
          .fill('<span></span>')
          .join('');

  event.style.height = numberOfLines*21 + "px";
}

function keydown(event){
  if (event.key === 'Tab') {
          const start = event.target.selectionStart;
          const end = event.target.selectionEnd;

          event.target.value = event.target.value.substring(0, start) + '\t' + event.target.value.substring(end);

          event.preventDefault();
        }
}

function Abrir(){
  var input = document.createElement('input');
  input.type = 'file';
  input.click();
  input.onchange = e => { 
    var file = e.target.files[0];
    var fr=new FileReader();
    fr.onload=function(){
      document.getElementById('entrada').value=fr.result.trim();
      keyup(document.getElementById("entrada"));
    }
    fr.readAsText(file); 
  }
  
}

function Enviar(){
  regreso = document.getElementById('entrada').value
  Toastify({
    text: "Ejecutando...",
    className: "info",
    gravity: "top",
    position: "center",
    style: {
      background: "#f17baf",

    }
  }).showToast();
  fetch(url+"comandos", {
    method: 'POST', // or 'PUT'
    mode: 'cors',
  headers: {
    'Access-Control-Allow-Origin':'*'
  },
    body: JSON.stringify(regreso),
     headers: {
                    'Content-Type': 'application/json',
                }
  }).then(function(response)
            {
                response.json().then(data=>{
                  document.getElementById('consola').value=data.consola;
                  keyup(document.getElementById("consola"));
                  for(rep of data.reportes){
                    lista_reportes.push(rep);
                  }
                  update_reportes()
                })
            }).catch(function(error)
            {
                console.log(error);
            });
}

function update_reportes(){
  html = ""
  for(let i= 0; i< lista_reportes.length;i++){
    html += " <button class=\"btn_rep\" onclick=\"mostrar_reporte("+i+",this)\">"+lista_reportes[i]["name"]+"</button>"
  }
  document.getElementById("selector_reporte").innerHTML = html;
}


function mostrar_reporte(indice,o){
  btns=document.getElementsByClassName("btn_rep");
  for(btn of btns){
    if(btn.classList.contains("focus")){
      btn.classList.toggle("focus");
    }
  }
  o.classList.toggle("focus");

  reporte = lista_reportes[indice];
  r_t = document.getElementById("editor_texto");
  l = document.getElementById("lienzo");
  
  if(reporte["tipo"] == "g"){
    
    if(!r_t.classList.contains("hidden")){
      r_t.classList.toggle("hidden");
    }
    if(l.classList.contains("hidden")){
      l.classList.toggle("hidden");
    }

    d3.select("#lienzo").graphviz()
      .width("48vw") 
      .height("90vh")
      .renderDot(reporte["rep"]);
  }else{
    if(!l.classList.contains("hidden")){
      l.classList.toggle("hidden");
    }
    if(r_t.classList.contains("hidden")){
      r_t.classList.toggle("hidden");
    }

    document.getElementById("reporte_t").value=reporte["rep"];
    keyup(document.getElementById("reporte_t"));
    
  }
}

function Login(){
  user = document.getElementById("txt_user").value;
  pass = document.getElementById("txt_pass").value;
  id_ = document.getElementById("txt_part").value;
  s = "login -user="+user+" -pass="+pass+" -id="+id_

  fetch(url+"logs", {
    method: 'POST', // or 'PUT'
    mode: 'cors',
  headers: {
    'Access-Control-Allow-Origin':'*'
  },
    body: JSON.stringify(s),
     headers: {
                    'Content-Type': 'application/json',
                }
  }).then(function(response)
            {
                response.json().then(data=>{
                  Toastify({
                    text: data.mensaje,
                    className: "info",
                    gravity: "top",
                    position: "center",
                    style: {
                      background: "#f17baf",
                    }
                  }).showToast();
                })
            }).catch(function(error)
            {
              Toastify({
                    text: error,
                    className: "info",
                    gravity: "top",
                    position: "center",
                    style: {
                      background: "#f17baf",
                    }
                  }).showToast();
            });
}

function Logout(){
  s = "logout"

  fetch(url+"logs", {
    method: 'POST', // or 'PUT'
    mode: 'cors',
  headers: {
    'Access-Control-Allow-Origin':'*'
  },
    body: JSON.stringify(s),
     headers: {
                    'Content-Type': 'application/json',
                }
  }).then(function(response)
            {
                response.json().then(data=>{
                  Toastify({
                    text: data.mensaje,
                    className: "info",
                    gravity: "top",
                    position: "center",
                    style: {
                      background: "#f17baf",
                    }
                  }).showToast();
                })
            }).catch(function(error)
            {
                Toastify({
                    text: error,
                    className: "info",
                    gravity: "top",
                    position: "center",
                    style: {
                      background: "#f17baf",
                    }
                  }).showToast();
            });
}