/**
 * tracingtool.js
 *
 * requirements:
 *	 tools.js
 *	 ui.js
 *	 slider.js
 *   stack.js
 */

/**
 */

/**
 * Tracing tool.
 */
function TracingTool()
{
  this.prototype = new Navigator();
  
  var self = this;
  var tracingLayer = null;
  var stack = null;

	this.resize = function( width, height )
	{
        self.prototype.resize( width, height );
		return;
	}

	/**
	 * install this tool in a stack.
	 * register all GUI control elements and event handlers
	 */
	this.register = function( parentStack )
	{

    // TODO: replace with project.js strings
    if ( self.prototype.stack == null ) {
      var box = $( '<div class="box" id="tracingbuttons"></div>' );
      [ { name : "skeleton", alt : "skeleton" },
        { name : "synapse", alt : "synapse" },
        { name : "goactive", alt : "go to active element" },
        { name : "skelsplitting", alt : "split skeleton" },
        { name : "skelrerooting", alt : "reroot skeleton" },
        { name : "togglelabels", alt : "toggle labels" },
        { name : "3dview", alt : "3d view" } ].map(
        function( button ) {
          var a = document.createElement('a');
          a.setAttribute('class', 'button');
          a.setAttribute('id', 'trace_button_' + button.name);
          a.onclick = function( e ) {
            tracingLayer.svgOverlay.tracingCommand(button.name);
            return false;
          };
          var img = document.createElement('img');
          img.setAttribute('title', button.alt);
          img.setAttribute('alt', button.alt);
          img.setAttribute('src', 'widgets/themes/kde/trace_' + button.name + '.png');
          a.appendChild(img);
          box.append(a);
        }
      );
      $( "#toolbar_nav" ).prepend( box );
    }

    // If the tracing layer exists and it belongs to a different stack, remove it
    if (tracingLayer && stack && stack !== parentStack) {
      stack.removeLayer( tracingLayer );
    }
    stack = parentStack;
    tracingLayer = new TracingLayer( parentStack );
    //this.prototype.mouseCatcher = tracingLayer.svgOverlay.getView();
    this.prototype.setMouseCatcher( tracingLayer.svgOverlay.view );
    parentStack.addLayer( "TracingLayer", tracingLayer );

    // Call register AFTER changing the mouseCatcher
    self.prototype.register( parentStack, "edit_button_trace" );

    // NOW set the mode TODO cleanup this initialization problem
    tracingLayer.svgOverlay.set_tracing_mode( "skeletontracing" );
    tracingLayer.svgOverlay.updateNodes();

    // view is the mouseCatcher now
    var view = tracingLayer.svgOverlay.view;

    var proto_onmousedown = view.onmousedown;
    view.onmousedown = function( e ) {
      switch ( ui.getMouseButton( e ) )
      {
        case 1:
          tracingLayer.svgOverlay.whenclicked( e );
          break;
        case 2:
          proto_onmousedown( e );
          ui.registerEvent( "onmousemove", updateStatusBar );
          ui.registerEvent( "onmouseup",
            function onmouseup (e) {
              ui.releaseEvents();
              ui.removeEvent( "onmousemove", updateStatusBar );
              ui.removeEvent( "onmouseup", onmouseup );
              // Recreate nodes by feching them from the database for the new field of view
              tracingLayer.svgOverlay.updateNodes();
            });
          break;
        default:
          proto_onmousedown( e );
          break;
      }
      return;
    };

    var proto_changeSlice = self.prototype.changeSlice;
    self.prototype.changeSlice =
      function( val ) {
        proto_changeSlice( val );
        tracingLayer.svgOverlay.updateNodes();
      };

    return;
  }

	/**
	 * unregister all stack related mouse and keyboard controls
	 */
	this.unregister = function()
	{
        // do it before calling the prototype destroy that sets stack to null
        if (self.prototype.stack) {
            self.prototype.stack.removeLayer( "TracingLayer" );
        }
        self.prototype.unregister();
        return;
	}

	/**
	 * unregister all project related GUI control connections and event
	 * handlers, toggle off tool activity signals (like buttons)
	 */
	this.destroy = function()
	{
        // Synchronize data with database
        tracingLayer.svgOverlay.updateNodeCoordinatesinDB();

        // the prototype destroy calls the prototype's unregister, not self.unregister
        // do it before calling the prototype destroy that sets stack to null
        self.prototype.stack.removeLayer( "TracingLayer" );
        self.prototype.destroy( "edit_button_trace" );
        $( "#tracingbuttons" ).remove();
        return;
	};


  var updateStatusBar = function( e ) {
    var m = ui.getMouse(e, true);
    var offX, offY, pos_x, pos_y;
    if (m) {
      // add right move of svgOverlay to the m.offsetX
      offX = m.offsetX + tracingLayer.svgOverlay.offleft;
      // add down move of svgOverlay to the m.offsetY
      offY = m.offsetY + tracingLayer.svgOverlay.offtop;

      // TODO pos_x and pos_y never change
      pos_x = stack.translation.x + (stack.x + (offX - stack.viewWidth / 2) / stack.scale) * stack.resolution.x;
      pos_y = stack.translation.x + (stack.y + (offY - stack.viewHeight / 2) / stack.scale) * stack.resolution.y;
      statusBar.replaceLast("[" + pos_x.toFixed(3) + ", " + pos_y.toFixed(3) + "]" + " stack.x,y: " + stack.x + ", " + stack.y);
    }
    return true;
  };
}

