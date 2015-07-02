/* Countdown timer */
function Countdown(duration, granularity) {
  this.duration = duration;
  this.granularity = granularity || 1000;
  this.tickCallbacks = [];
  this.expireCallbacks = [];
  this.running = false;
  this._timeout = null;
}

Countdown.prototype.start = function() {
  if (this.running) { return; }
  this.running = true;
  var start = Date.now(),
      self = this,
      diff;

  (function timer() {
    diff = self.duration - (((Date.now() - start) / 1000) | 0);

    if (diff > 0) {
      self._timeout = setTimeout(timer, self.granularity);
    } else {
      diff = 0;
      self.running = false;
      self._timeout = null;
    }

    self.tickCallbacks.forEach(function(f) {
      f.call(this, diff);
    }, self);

    if (diff <= 0) {
    self.expireCallbacks.forEach(function(f) {
        f.call(this);
      }, self);
    };

  }());
};

Countdown.prototype.stop = function() {
  if (!this.running) { return; }
  if (this._timeout != null) {
    clearTimeout(this._timeout);
    this._timeout = null;
  }
  this.running = false;
}

Countdown.prototype.restart = function() {
  this.stop();
  this.start();
}

Countdown.prototype.onTick = function(f) {
  if (typeof f === 'function') {
    this.tickCallbacks.push(f);
  }
  return this;
};

Countdown.prototype.onExpire = function(f) {
  if (typeof f === 'function') {
    this.expireCallbacks.push(f);
  }
  return this;
}

Countdown.prototype.expired = function() {
  return !this.running;
};

/* Templates */

var nodeFactory = new (function(){
	var self = this;
	return self = {
		templates: {
			'post': '<div class="post" data-post-id="{{ id }}"><div class="header"><label><span class="topic">{{ topic }}</span> <span class="author_name">{{ author_name }}</span> <span class="date">{{ created_at }}</span> </label><span class="reflink">#{{ id }}</span></div><div class="attachments"></div><div class="text">{{ text }}</div></div>'
		},
		
		buildFromData: function buildFromData(template_name, data) {
			var node = $(self.templates[template_name]);
			if (template_name == 'post') {
				node.attr('data-post-id', data.id);
				node.find('.header .topic').html(data.topic);
				node.find('.header .author_name').html(data.author_name || 'Аноним');
				node.find('.header .date').html(data.created_at);
				node.find('.header .reflink').html('#' + data.id);
				node.find('.text').html(data.text);
			} else {
				throw new Error('No such template: ' + template_name);
			}
			return node;
		}
	};
})();

/* Settings */

var userSettings = {
	'autoupdate': true,
	'autoupdate_board': false,
	'autoupdate_interval': 10
};

/* Application */

var App = function(){
	var self = this;
	return self = {
		
		config: {},
		
		getThreadPostsAfter: function getThreadPostsAfter(thread_id, last_post_id) {
			return $.getJSON(
				'/api/threads/' + thread_id + '/posts/after/' + last_post_id
			);
		},
		
		updateThreads: function() {
			var threads = $('.thread');
			
			threads.each(function(index){
				var thread = $(this);
				var thread_id = thread.attr('data-thread-id');
				var last_post_id = thread.find('.post').last().attr('data-post-id');
				
				// Optionally update thread previews on board page; TODO
				if (thread.hasClass('preview') && userSettings.autoupdate_board) {
					self.getThreadPostsAfter(thread_id, last_post_id)
					.done(function(response) {
						if (!response.posts) { return; }
						var posts = response.posts.slice(-self.config.THREAD_PREVIEW_POSTS_COUNT);
						var delete_count = Math.min(thread.find('.post').length - 1, posts.length);
						
						// TODO: nice animations
						thread.find('.post').slice(1, 1 + delete_count).remove();
						
						for (var i = 0; i < posts.length; ++i) {
							var post = nodeFactory.buildFromData('post', posts[i]);
							thread.append(post);
						}
			
					});
				} else {
					self.getThreadPostsAfter(thread_id, last_post_id)
						.done(function(response) {
							if (!response.posts) { return; }
							for (var i = 0; i < response.posts.length; ++i) {
								var post = nodeFactory.buildFromData('post', response.posts[i]);
								// TODO: nice animations
								post.css('display', 'none');
								thread.append(post);
								post.fadeIn();
							}
							self.autoupdateCountdown.start();
						})
						.error(function() {
							self.autoupdateCountdown.start();
						});
				}
			})
		},
		
		init: function() {
			console.log('initializing');
			if (userSettings.autoupdate) {
				this.autoupdateCountdown = new Countdown(userSettings.autoupdate_interval, 1000)
					.onTick(function(remaining) {
						$('.autoupdate-countdown').html('Автообновление через ' + remaining.toString());
					})
					.onExpire(function() {
						try {
							$('.autoupdate-countdown').html('Автообновление...');
							self.updateThreads();
						} catch(e) {
							
						}
					});
				this.autoupdateCountdown.start();
			}
		}
	};
};

// Some settings are set in base.html template, so app must be accessible from global scope
app = new App();

$(document).ready(function() {
	app.init();
	$('.autoupdate-toggle').prop('checked', userSettings.autoupdate === true);

	/* Posting form */
	$('.posting-form-toggle').each(function() {
		$this = $(this);
		$this.html('[ ' + $this.attr('data-message-on') + ' ]');
		$this.attr('data-form-open', false);
	});

	$('.posting-form-toggle').on('click', function() {
		$this = $(this);
		$posting_form = $this.next('.posting-form');
		
		if ($this.attr('data-form-open') == 'false') {
			$this.html('[ ' + $this.attr('data-message-off') + ' ]');
			$posting_form.show();
			$this.attr('data-form-open', true);
		} else {
			$this.html('[ ' + $this.attr('data-message-on') + ' ]');
			$posting_form.hide();
			$this.attr('data-form-open', false);
		}
		
	});

	/* Youtube previews */
	$('.yt-preview').on('click', function() {
		$this = $(this);
		$video = $this.next('.yt-player');
		$video.show();
		$this.hide();
	});

	/* Autoupdating */
	
	$autoupdate_toggles = $('input[type="checkbox"].autoupdate-toggle')
	$autoupdate_toggles.on('change', function() {
		$this = $(this);
		if ($this.is(':checked')) {
			app.autoupdateCountdown.start();
			$autoupdate_toggles.prop('checked', true);
		} else {
			app.autoupdateCountdown.stop();
			$autoupdate_toggles.prop('checked', false);
			$autoupdate_toggles.next('.autoupdate-countdown').html('Автообновление');
		}
	});
	
	/* Post links (works for dynamic elements) */
	
	$('thread').on('mouseover', 'a.postlink', function() {
		// TODO
	});

});