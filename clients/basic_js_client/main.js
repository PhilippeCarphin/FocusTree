var ftserver_token
var tree = null
const fileSelector = document.getElementById('ftserver-token');

async function periodicUpdates(){
    updateViews()
}

function init(){
    fileSelector.addEventListener('change', function() {
        var fr = new FileReader();
        fr.onload = function(){
            ftserver_token = fr.result;
        }
        fr.readAsText(this.files[0])
    });
    updateViews()
    setInterval(periodicUpdates, 60*1000);
    document.getElementById('command').addEventListener('keypress', (event) => {
        if(event.key === "Enter"){
            event.preventDefault()
            sendCommand()
        }
    })
}

let sendCommand = function(){
    let req = new XMLHttpRequest();
    req.onreadystatechange = function(){
        if(this.readyState != 4){return;}
        if(this.status != 200){console.log(this); return;}

        resp = JSON.parse(this.responseText);
        document.getElementById('errors').innerHTML = resp.error;
        document.getElementById('output').innerHTML = resp.term_output;

        updateViews()
    };

    req.open('POST', '../api/send-command');
    req.setRequestHeader("Content-type", "text/text");
    command = document.getElementById('command')
    obj = {
        "command": command.value,
        "args": "",
        "token": ftserver_token,
        "html": true
    }
    command.value = ""
    console.log("command.value: ", command.value)
    console.log("Sending command: ", obj)
    req.send(JSON.stringify(obj, null, 2));
};
/*
 * Create a ul whose li are the children of obj recursively
 */
function to_ul (obj, currentTaskId) {
  var i, li, ul = document.createElement ("ul");
  obj.children.forEach((child) => {
    li = document.createElement ("li");
    li.appendChild(document.createTextNode("[" + child.id + "] " + child.text));
    if(child.id == currentTaskId){
        // li.style.color = "yellow"
        li.className = "current-task"
        // li.style.border = "thin solid purple"
    } else if(child.info.done){
        li.style.color = "green"
    } else {
        li.style.color = "red"
    }
    li.appendChild (to_ul (child, currentTaskId));
    ul.appendChild (li);
  })
  return ul;
}
let updateViews = function(){
    let req = new XMLHttpRequest();
    req.onreadystatechange = function(){
        if(this.readyState != 4){return;}
        if(this.status != 200){console.log(this); return;}

        tree = JSON.parse(this.responseText);
        // the current task view uses tree.current_task_id
        // which is dependant on the api/tree request having
        // been completed.  Perhaps this is a flaw.
        updateCurrentTask()
        const tree_div = document.getElementById("tree")
        tree_div.innerHTML = ""
        tree_div.appendChild(to_ul({"children": tree.root_nodes}, tree.current_task_id))
    };
    req.open('GET', '../api/tree');
    req.send();
};
function lineTree(array){
    mainList = document.createElement("div")
    var current = mainList
    array.forEach((t) => {
        ul = document.createElement("ul")

        li = document.createElement("li");
        li.appendChild(document.createTextNode("[" + t.id + "] " + t.text));
        ul.appendChild(li)

        current.appendChild(ul)
        current = li
    })
    return mainList
}


let updateCurrentTask = function(){
    const req = new XMLHttpRequest();
    req.open('GET', '../api/current', true);
    req.onreadystatechange = function(){
        if(this.readyState != 4){return;}
        if(this.status != 200){console.log(this); return;}
        const resp = JSON.parse(this.responseText)
        currentTaskDiv = document.getElementById('current-task')
        currentTaskDiv.innerHTML = ""
        currentTaskDiv.appendChild(to_ul({"children": [resp]}, tree.current_task_id))
        // document.getElementById('current-task').innerHTML = resp.term_output;
    };
    req.send();
};

init()
