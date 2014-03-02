// iMouseDown represents the current mouse button state: up or down
/*
lMouseState represents the previous mouse button state so that we can
check for button clicks and button releases:
if(iMouseDown && !lMouseState) // button just clicked!
if(!iMouseDown && lMouseState) // button just released!
*/
var mouseOffset = null;
var iMouseDown  = false;
var lMouseState = false;
var dragObject  = null;
// Demo 0 variables
var DragDrops   = [];
var curTarget   = null;
var lastTarget  = null;
var dragHelper  = null;
var tempDiv     = null;
var rootParent  = null;
var rootSibling = null;
var dropTargets = [];
Number.prototype.NaN0=function(){return isNaN(this)?0:this;}
function CreateDragContainer(){
	/*
	Create a new "Container Instance" so that items from one "Set" can not
	be dragged into items from another "Set"
	*/
	var cDrag        = DragDrops.length;
	DragDrops[cDrag] = [];
	/*
	Each item passed to this function should be a "container".  Store each
	of these items in our current container
	*/
	for(var i=0; i<arguments.length; i++){
		var cObj = arguments[i];
		DragDrops[cDrag].push(cObj);
		cObj.setAttribute('DropObj', cDrag);
		/*
		Every top level item in these containers should be draggable.  Do this
		by setting the DragObj attribute on each item and then later checking
		this attribute in the mouseMove function
		*/
		for(var j=0; j<cObj.childNodes.length; j++){
			// Firefox puts in lots of #text nodes...skip these
			if(cObj.childNodes[j].nodeName=='#text') continue;
			cObj.childNodes[j].setAttribute('DragObj', cDrag);
		}
	}
}

function addDropTarget(dropTarget){
    dropTargets.push(dropTarget);
}
function makeClickable(object){
    object.onmousedown = function(){
        dragObject = this;
    }
}
function getMouseOffset(target,ev){
    ev = ev ||window.event;
    var docPos = getPosition(target);
    var mousePos = mouseCoords(ev);
    return {x:mousePos.x - docPos.x,y:mousePos.y - docPos.y};
}
function getPosition(e){
    var left = 0;
    var top = 0;
    while(e.offsetParent){
        left+=e.offsetLeft;
        top +=e.offsetTop;
        e = e.offsetParent;
    }
    left+=e.offsetLeft;
    top+=e.offsetTop;
    return {x:left,y:top};
}

function makeDraggable(item){
    if(!item) return;
    item.onmousedown = function(ev){
        dragObject = this;
        mouseOffset = getMouseOffset(this,ev);
        return false;
    }
}

function mouseMove(ev){
	ev         = ev || window.event;
	/*
	We are setting target to whatever item the mouse is currently on
	Firefox uses event.target here, MSIE uses event.srcElement
	*/
	var target   = ev.target || ev.srcElement;
	var mousePos = mouseCoords(ev);
	// mouseOut event - fires if the item the mouse is on has changed
	if(lastTarget && (target!==lastTarget)){
		// reset the classname for the target element
		var origClass = lastTarget.getAttribute('origClass');
		if(origClass) lastTarget.className = origClass;
	}
	/*
	dragObj is the grouping our item is in (set from the createDragContainer function).
	if the item is not in a grouping we ignore it since it can't be dragged with this
	script.
	*/
	var dragObj = target.getAttribute('DragObj');
	 // if the mouse was moved over an element that is draggable
	if(dragObj!=null){
		// mouseOver event - Change the item's class if necessary
		if(target!=lastTarget){
			var oClass = target.getAttribute('overClass');
			if(oClass){
				target.setAttribute('origClass', target.className);
				target.className = oClass;
			}
		}
		// if the user is just starting to drag the element
		if(iMouseDown && !lMouseState){
			// mouseDown target
			curTarget     = target;
			// Record the mouse x and y offset for the element
			rootParent    = curTarget.parentNode;
			rootSibling   = curTarget.nextSibling;
			mouseOffset   = getMouseOffset(target, ev);
			// We remove anything that is in our dragHelper DIV so we can put a new item in it.
			for(var i=0; i<dragHelper.childNodes.length; i++) dragHelper.removeChild(dragHelper.childNodes[i]);
			// Make a copy of the current item and put it in our drag helper.
			dragHelper.appendChild(curTarget.cloneNode(true));
			dragHelper.style.display = 'block';
			// set the class on our helper DIV if necessary
			var dragClass = curTarget.getAttribute('dragClass');
			if(dragClass){
				dragHelper.firstChild.className = dragClass;
			}
			// disable dragging from our helper DIV (it's already being dragged)
			dragHelper.firstChild.removeAttribute('DragObj');
			/*
			Record the current position of all drag/drop targets related
			to the element.  We do this here so that we do not have to do
			it on the general mouse move event which fires when the mouse
			moves even 1 pixel.  If we don't do this here the script
			would run much slower.
			*/
			var dragConts = DragDrops[dragObj];
			/*
			first record the width/height of our drag item.  Then hide it since
			it is going to (potentially) be moved out of its parent.
			*/
			curTarget.setAttribute('startWidth',  parseInt(curTarget.offsetWidth));
			curTarget.setAttribute('startHeight', parseInt(curTarget.offsetHeight));
			curTarget.style.display  = 'none';
			// loop through each possible drop container
			for(var i=0; i<dragConts.length; i++){
				with(dragConts[i]){
					var pos = getPosition(dragConts[i]);
					/*
					save the width, height and position of each container.
					Even though we are saving the width and height of each
					container back to the container this is much faster because
					we are saving the number and do not have to run through
					any calculations again.  Also, offsetHeight and offsetWidth
					are both fairly slow.  You would never normally notice any
					performance hit from these two functions but our code is
					going to be running hundreds of times each second so every
					little bit helps!
					Note that the biggest performance gain here, by far, comes
					from not having to run through the getPosition function
					hundreds of times.
					*/
					setAttribute('startWidth',  parseInt(offsetWidth));
					setAttribute('startHeight', parseInt(offsetHeight));
					setAttribute('startLeft',   pos.x);
					setAttribute('startTop',    pos.y);
				}
				// loop through each child element of each container
				for(var j=0; j<dragConts[i].childNodes.length; j++){
					with(dragConts[i].childNodes[j]){
						if((nodeName=='#text') || (dragConts[i].childNodes[j]==curTarget)) continue;
						var pos = getPosition(dragConts[i].childNodes[j]);
						// save the width, height and position of each element
						setAttribute('startWidth',  parseInt(offsetWidth));
						setAttribute('startHeight', parseInt(offsetHeight));
						setAttribute('startLeft',   pos.x);
						setAttribute('startTop',    pos.y);
					}
				}
			}
		}
	}
	// If we get in here we are dragging something
	if(curTarget){
		// move our helper div to wherever the mouse is (adjusted by mouseOffset)
        var top_temp = mousePos.y - mouseOffset.y;
        var left_temp= mousePos.x - mouseOffset.x;
		dragHelper.style.top  = top_temp.toString().concat("px");
		dragHelper.style.left = left_temp.toString().concat("px");
		var dragConts  = DragDrops[curTarget.getAttribute('DragObj')];
		var activeCont = null;
		var xPos = mousePos.x - mouseOffset.x + (parseInt(curTarget.getAttribute('startWidth')) /2);
		var yPos = mousePos.y - mouseOffset.y + (parseInt(curTarget.getAttribute('startHeight'))/2);
		// check each drop container to see if our target object is "inside" the container
		for(var i=0; i<dragConts.length; i++){
			with(dragConts[i]){
				if(((getAttribute('startLeft'))                               < xPos) &&
					((getAttribute('startTop'))                                < yPos) &&
					((getAttribute('startLeft') + getAttribute('startWidth'))  > xPos) &&
					((getAttribute('startTop')  + getAttribute('startHeight')) > yPos)){
						/*
						our target is inside of our container so save the container into
						the activeCont variable and then exit the loop since we no longer
						need to check the rest of the containers
						*/
						activeCont = dragConts[i];
						// exit the for loop
				}
			}
		}
		// Our target object is in one of our containers.  Check to see where our div belongs
		if(activeCont){
			// beforeNode will hold the first node AFTER where our div belongs
			var beforeNode = null;
			// loop through each child node (skipping text nodes).
			for(var i=activeCont.childNodes.length-1; i>=0; i--){
				with(activeCont.childNodes[i]){
					if(nodeName=='#text') continue;
					// if the current item is "After" the item being dragged
					if(
						curTarget != activeCont.childNodes[i]                              &&
						((getAttribute('startLeft') + getAttribute('startWidth'))  > xPos) &&
						((getAttribute('startTop')  + getAttribute('startHeight')) > yPos)){
							beforeNode = activeCont.childNodes[i];
					}
				}
			}
			// the item being dragged belongs before another item
			if(beforeNode){
				if(beforeNode!=curTarget.nextSibling){
					activeCont.insertBefore(curTarget, beforeNode);
				}
			// the item being dragged belongs at the end of the current container
			} else {
				if((curTarget.nextSibling) || (curTarget.parentNode!=activeCont)){
					activeCont.appendChild(curTarget);
				}
			}
			// make our drag item visible
			if(curTarget.style.display!=''){
				curTarget.style.display  = '';
			}
		} else {
			// our drag item is not in a container, so hide it.
			if(curTarget.style.display!='none'){
				curTarget.style.display  = 'none';
			}
		}
	}
	// track the current mouse state so we can compare against it next time
	lMouseState = iMouseDown;
	// mouseMove target
	lastTarget  = target;
	// track the current mouse state so we can compare against it next time
	lMouseState = iMouseDown;
	// this helps prevent items on the page from being highlighted while dragging
	return false;
}

function mouseCoords(ev){
    if(ev.pageX || ev.pageY){
        return {x:ev.pageX, y:ev.pageY};
    }
    return {
        x:ev.clientX + document.body.scrollLeft - document.body.clientLeft,
        y:ev.clientY + document.body.scrollTop - document.body.clientTop
    };
}

function mouseUp(ev){
	if(curTarget){
		// hide our helper object - it is no longer needed
		dragHelper.style.display = 'none';
		// if the drag item is invisible put it back where it was before moving it
		if(curTarget.style.display == 'none'){
			if(rootSibling){
				rootParent.insertBefore(curTarget, rootSibling);
			} else {
				rootParent.appendChild(curTarget);
			}
		}
		// make sure the drag item is visible
		curTarget.style.display = '';
	}
	curTarget  = null;
	iMouseDown = false;
}
function mouseDown(){
	iMouseDown = true;
	if(lastTarget){
		return false;
	}
}
document.onmousemove = mouseMove;
document.onmousedown = mouseDown;
document.onmouseup   = mouseUp;
