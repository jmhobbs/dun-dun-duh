jQuery(function ($) {

	var working_messages = [
		"Uploading Pixels",
		"Grokking Polar Coordinates",
		"Reticulating Splines",
		"Adjusting Bell Curves",
		"Tweeting Your Home Address",
		"Googling For Jokes",
		"Blitting Image Maps",
		"Starting Photoshop",
		"Enhancing EXIF Data",
		"Licensing GIF89a",
		"Booting Gaussian Blur Kernel",
		"Blogging Haar Cascades"
	];

	var ddd = {},
      upload = $('#file').fileupload({
				url: DDD_UPLOAD_URL,
				dataType: 'json',
				formData: {"upload_token": DDD_UPLOAD_TOKEN},
				singleFileUploads: true,
				maxNumberOfFiles: 1,
				acceptFileTypes: /(\.|\/)(gif|jpe?g|png)$/i,
				change: function (e, data) {
					var file = data.files[0];
					$('#upload-help').removeClass('error').text('');
					if (!(/\.(gif|jpe?g|png)$/i).test(file.name)) {
						$('#upload-help').addClass('error').text("Please select an image file. (jpg, gif, png)");
            return false;
					}
					else if (file.size > 6291456) {
						$('#upload-help').addClass('error').text("Please choose a smaller image. The largest acceptable size is 6MB.");
						return false;
					}
				},
				submit: function (e, data) {
					$("#upload-row").hide();
					$("#progress-row").show();
				},
				done: function (e, data) {
					if( data.result.error === false ) {
						$("#progress-text").text("Please Wait");
						ddd.id = data.result.files[0].id;
						setUpCrop(data.result.files[0].src);
					}
					else {
						$('#progress-row').hide();
						$('#error-details').text(data.result.error);
						$('#error-row').show();
					}
				},
				fail: function (e, data) {
					$('#upload-row').hide();
					$('#progress-row').hide();
					$('#error-row').show();
				},
				progressall: function (e, data) {
					var progress = parseInt(data.loaded / data.total * 100, 10);
					$('#progress .progress-bar').css('width', progress + '%');
					$("#progress-status").text(progress + "%");
				}
			});

		function setUpCrop (src) {
			$('#crop-image')
				.on('load', function () {
					$("#progress-row").hide();
					$('#crop-row').show();

					$("#step-1").removeClass("active");
					$("#step-2").addClass("active");

					var $img = $(this),
							width = $img.width(),
							height = $img.height(),
							size, max_size, x, y;

					if( width < height ) {
						size = Math.max(10, Math.floor(width * 0.5));
						max_size = Math.max(10, Math.floor(width * 0.75));
					}
					else {
						size = Math.max(10, Math.floor(height * 0.5));
						max_size = Math.max(10, Math.floor(height * 0.75));
					}

					x = Math.floor((width - size) / 2);
					y = Math.floor((height - size) / 2);

					$(this).Jcrop({
						aspectRatio: 1,
						minSize: [10, 10],
						maxSize: [max_size, max_size],
						allowSelect: false,
						setSelect: [x, y, x + size, y + size],
						onSelect: function (c) {
							ddd.x = c.x;
							ddd.y = c.y;
							ddd.size = c.w;
							$("#make-the-gif-dude").attr('disabled', false);
						}
					});
				})
				.on('error', function () {
					$("#progress-row").hide();
					$('#error-row').show();
				})
				.attr("src", src);
		}

		$("#make-the-gif-dude").on("click", function (e) {
			e.preventDefault();
			if( $(this).is(":disabled") ) { return; }

			ddd.final_frame = $("#final-frame").val();

			$("#crop-row").hide();
			
			$(".progress-bar").css("width", "100%");
			$("#progress-text").text("");
			$("#progress-row").show();

			$("#step-2").removeClass("active");
			$("#step-3").addClass("active");

			updateCropProgressMessage();

			$.post(DDD_COMPOSE_URL, ddd)
				.success(function (data) {
					ddd.job_id = data.job_id;
					checkJob();
				})
				.error(function (e) {
					$("#progress-row").hide();
					$("#error-row").show();
				});
		});

		function updateCropProgressMessage () {
			$('#progress-text').fadeOut('fast', function () {
				$(this).text(working_messages[Math.floor(Math.random() * working_messages.length)]);
				$(this).fadeIn('fast');
			});
		}

		var job_checks = 0;

		function checkJob () {
			updateCropProgressMessage();
			$.getJSON(
				DDD_JOB_STATUS_URL,
				{id: ddd.job_id}
			)
			.success(function (data) {
				if( data.error ) {
					$('#progress-row').hide();
					$('#error-row').show();
				}
				else {
					if( data.data.failed ) {
						$('#progress-row').hide();
						$('#error-row').show();
					}
					else if( data.data.finished ) {
						window.location.href = data.data.return_value.view_url;
					}
					else {
						if( ++job_checks > 10 ) {
							$('#progress-row').hide();
							$('#error-row').show();
							$.getJSON(
								DDD_JOB_CANCEL_URL,
								{id: ddd.job_id}
							);
						}
						else {
							setTimeout(checkJob, 1000);
						}
					}
				}
			})
			.error(function (e) {
				$('#progress-row').hide();
				$('#error-row').show();
			});
		}

});
