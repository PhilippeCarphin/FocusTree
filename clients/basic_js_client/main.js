
const displayErrors = function(errorMessage){
    document.getElementById('errors').innerHTML = errorMessage;
};

console.log("MAIN.JS")

let sendCommand = function(){
    let req = new XMLHttpRequest();
    req.onreadystatechange = function(){
        if(this.readyState != 4){return;}
        if(this.status != 200){console.log(this); return;}

        resp = JSON.parse(this.responseText);
        console.log("resp: ", resp);
        document.getElementById('errors').innerHTML = resp.error;
        document.getElementById('output').innerHTML = resp.term_output;

        updateTreeView();
        updateCurrentTask();
    };

    req.open('POST', '/api/send-command');
    req.setRequestHeader("Content-type", "text/text");
    const command = document.getElementById('command').value;
    console.log("sending command ....");
    console.log(command);
    obj = {
        "command": command,
        "args": ""
    }
    console.log(obj);
    console.log(JSON.stringify(obj, null, 2))
    req.send(JSON.stringify(obj, null, 2));
};
/*
 * Create a ul whose li are the children of obj recursively
 */
function to_ul (obj, currentTaskId) {
  var i, li, ul = document.createElement ("ul");
  obj.children.forEach((child) => {
      console.log(child)
    li = document.createElement ("li");
    li.appendChild(document.createTextNode("[" + child.id + "] " + child.text));
    if(child.id == currentTaskId){
        li.style.color = "purple"
        li.style.border = "thin solid purple"
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
let updateTreeView = function(){
    let req = new XMLHttpRequest();
    req.onreadystatechange = function(){
        if(this.readyState != 4){return;}
        if(this.status != 200){console.log(this); return;}

        const tree = JSON.parse(this.responseText);
        const tree_div = document.getElementById("tree")
        tree_div.innerHTML = ""
        tree_div.appendChild(to_ul({"children": tree.root_nodes}, tree.current_task_id))
    };
    req.open('GET', '/api/tree');
    req.send();
};
updateTreeView();

let updateCurrentTask = function(){
    const req = new XMLHttpRequest();
    req.open('POST', '/api/send-command', true);
    req.onreadystatechange = function(){
        if(this.readyState != 4){return;}
        if(this.status != 200){console.log(this); return;}
        const resp = JSON.parse(this.responseText)
        document.getElementById('current-task').innerHTML = resp.term_output;
    };
    obj = {
        "command": "current",
        "args": ""
    }
    console.log(obj);
    console.log(JSON.stringify(obj, null, 2))
    req.send(JSON.stringify(obj, null, 2));
};
updateCurrentTask();
