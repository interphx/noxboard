var nodeFactory = new (function(){
	var self = this;
	return self = {
		templates: {
			'post': '<div class="post" data-post-id="{{ id }}"><div class="header"><label><span class="topic">{{ topic }}</span> <span class="author_name">{{ author_name }}</span> <span class="date">{{ created_at }}</span> </label><span class="reflink">#{{ id }}</span></div><div class="attachments"></div><div class="text">{{ text }}</div></div>'
		},
		
		buildFromData: function buildFromData(template_name, data) {
			console.log(this);
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

var userSettings = {
	'autoupdate': true,
	'autoupdate_board': false,
	'autoupdate_interval': 10000
};


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
				
				// Optionally update thread previews on board page
				if (thread.hasClass('preview') && userSettings.autoupdate_board) {
					self.getThreadPostsAfter(thread_id, last_post_id)
					.done(function(json) {
						if (!json.posts) { return; }
						var posts = json.posts.slice(-self.config.THREAD_PREVIEW_POSTS_COUNT);
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
					.done(function(json) {
						if (!json.posts) { return; }
						for (var i = 0; i < json.posts.length; ++i) {
							var post = nodeFactory.buildFromData('post', json.posts[i]);
							// TODO: nice animations
							post.css('display', 'none');
							thread.append(post);
							post.fadeIn();
						}
					});
				}
			})
		},
		
		init: function() {
			console.log('initializing');
			if (userSettings.autoupdate) {
				setInterval(this.updateThreads, userSettings.autoupdate_interval);
			}
		}
	};
};

app = new App();
app.init();

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
})