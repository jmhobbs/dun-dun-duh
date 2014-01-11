module.exports = function(grunt) {
	grunt.loadNpmTasks('grunt-contrib-less');
	grunt.loadNpmTasks('grunt-contrib-jshint');
	grunt.loadNpmTasks('grunt-contrib-uglify');

	grunt.initConfig({
		less: {
			production: {
				options: {
					paths: ["dundunduh/static/src/"],
					cleancss: true
				},
				files: {
					"dundunduh/static/build/style.css": "dundunduh/static/src/style.less"
				}
			}
		},
		jshint: {
			all: ["dundunduh/static/src/*.js"]
		},
		uglify: {
			index: {
				files: {
					'dundunduh/static/build/index.min.js': ['dundunduh/static/src/index.js']
				},
				mangle: {
					except: ['ddd', 'jQuery']
				}
			}
		}
	});

	grunt.registerTask('default', ['less:production', "uglify:index", "jshint:all"]);
};
