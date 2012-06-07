(function() {
	var events;
	var check = function(e) {
		var target = $(e.target);
		var parents = target.getParents();
		events.each(function(item) {
			var element = item.element;
			if (element != target && !parents.contains(element))
				item.fn.call(element, e);
		});
	};

	Element.Events.outerClick = {
		onAdd : function(fn) {
			if (!events) {
				document.addEvent('click', check);
				events = [];
			}
			events.push( {
				element : this,
				fn : fn
			});
		},

		onRemove : function(fn) {
			events = events.filter(function(item) {
				return item.element != this || item.fn != fn;
			}, this);
			if (!events.length) {
				document.removeEvent('click', check);
				events = null;
			}
		}
	};

})();

var ScrollSpy = new Class( {
	Implements : [ Options, Events ],
	options : {
		min : 0,
		mode : "vertical",
		max : 0,
		container : window,
		onEnter : Function.from(),
		onLeave : Function.from(),
		onTick : Function.from()
	},
	initialize : function(b) {
		this.setOptions(b);
		this.container = $(this.options.container);
		this.enters = this.leaves = 0;
		this.max = this.options.max;
		if (this.max == 0) {
			var c = this.container.getScrollSize();
			this.max = this.options.mode == "vertical" ? c.y : c.x;
		}
		this.addListener();
	},
	addListener : function() {
		this.inside = false;
		this.container.addEvent("scroll", function() {
			var b = this.container.getScroll();
			var c = this.options.mode == "vertical" ? b.y : b.x;
			if (c >= this.options.min && c <= this.max) {
				if (!this.inside) {
					this.inside = true;
					this.enters++;
					this.fireEvent("enter", [ b, this.enters ]);
				}
				this.fireEvent("tick", [ b, this.inside, this.enters,
						this.leaves ]);
			} else {
				if (this.inside) {
					this.inside = false;
					this.leaves++;
					this.fireEvent("leave", [ b, this.leaves ]);
				}
			}
		}.bind(this));
	}
});

window.addEvent('domready', function() {

	var topbar = $('header').set('tween', {
		duration : 200
	});
	var backToTop = $('toTop').set('tween', {
		duration : 200
	});
	backToTop.setStyle('opacity', 0);
	backToTop.addEvent('click', function(e){
		(e).stop();
		window.scroll(0,0);
	})
	
	var topbarME = function() {
		topbar.tween('opacity', 1);
	}, topbarML = function() {
		topbar.tween('opacity', 0.5);
	}, ws = window.getScrollSize().y;
	var ss = new ScrollSpy( {
		min : 30,
		max : ws - 30,
		onLeave : function(pos) {
			topbar.tween('opacity', 1).removeEvents('mouseenter', topbarME)
					.removeEvents('mouseleave', topbarML);
			backToTop.tween('opacity', 0);
		},
		onEnter : function() {
			topbar.tween('opacity', 0.5).addEvent('mouseenter', topbarME)
					.addEvent('mouseleave', topbarML);
			backToTop.tween('opacity', 1);
		}
	});
	
	$(document.body).getElements('.disabled').setStyle('opacity', 0.2)
        
        // Fix for webapp, iPhone treats a's as a popup to safari. Make sure we change the location of THIS window on non blank targets
        var a=document.getElementsByTagName("a");
        for(var i=0;i<a.length;i++)
        { 
            if (a[i].target != '_blank') {
                a[i].onclick=function()
                {
                    window.location=this.getAttribute("href");
                    return false
                }
            }
        }
})
