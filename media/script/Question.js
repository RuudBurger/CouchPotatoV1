var Question = new Class( {

	initialize : function(question, answers) {
		var self = this

		self.question = question
		self.answers = answers

		self.createQuestion()
		self.answers.each(function(answer) {
			self.createAnswer(answer)
		})
		self.createMask()

	},

	createMask : function() {
		var self = this

		$(document.body).mask( {
			'hideOnClick' : true,
			'destroyOnHide' : true,
			'onHide' : function() {
				self.container.destroy();
			}
		}).show();
	},

	createQuestion : function() {

		this.container = new Element('div', {
			'class' : 'question'
		}).adopt(new Element('h3', {
			'text' : this.question
		})).inject(document.body)

		this.container.position( {
			'position' : 'center'
		});

	},

	createAnswer : function(options) {
		var self = this

		var answer = new Element('a', Object.merge(options, {
			'class' : 'answer '+options['class']
		})).inject(this.container)

		if (options.cancel) {
			answer.addEvent('click', self.close.bind(self))
		}

		if (options.ajax) {
			answer.addEvent('click', function(e){
				e.stop();
				new Request({
					'url': options.href,
					'onSuccess': function() {
						options.obj.getParent('.item').destroy();
						self.close();
					}
				}).send();	
			});
		}
	},

	close : function() {
		$(document.body).get('mask').destroy();
	},

	toElement : function() {
		return this.container
	}

})
