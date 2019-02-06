console.log("MAIN.JS");

const displayErrors = function(errorMessage){
    document.getElementById('errors').innerHTML = errorMessage;
};


let sendCommand = function(){
    let req = new XMLHttpRequest();
    req.onreadystatechange = function(){
        if(this.readyState != 4){return;}
        if(this.status != 200){console.log(this); return;}

        responseObject = JSON.parse(this.responseText);
        console.log(responseObject);
        console.log("DID I GET HERE");
        document.getElementById('errors').innerHTML = responseObject.errors;

        updateTreeView();
        updateCurrentTask();
    };

    req.open('POST', '/send-command');
    req.setRequestHeader("Content-type", "text/text");
    const command = document.getElementById('command').value;
    console.log("sending command ....");
    console.log(command);
    req.send(command);
};

let updateTreeView = function(){
    let req = new XMLHttpRequest();
    req.onreadystatechange = function(){
        if(this.readyState != 4){return;}
        if(this.status != 200){console.log(this); return;}

        document.getElementById("output").innerHTML = this.responseText;
    };
    req.open('GET', '/fuck_my_face');
    req.send();
};
// updateTreeView();

let updateCurrentTask = function(){
    const req = new XMLHttpRequest();
    req.open('GET', '/current-task', true);
    req.onreadystatechange = function(){
        if(this.readyState != 4){return;}
        if(this.status != 200){console.log(this); return;}

        document.getElementById('current-task').innerHTML = this.responseText;

    };
    req.send();
};
// updateCurrentTask();
