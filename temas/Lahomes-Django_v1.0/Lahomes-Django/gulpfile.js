////////////////////////////////
// Setup
////////////////////////////////

// Gulp and package
const {src, dest, parallel, series, watch} = require('gulp');
const pjson = require('./package.json');

// Plugins
const autoprefixer = require('autoprefixer');
const browserSync = require('browser-sync').create();
const concat = require('gulp-concat');
const tildeImporter = require('node-sass-tilde-importer');
const cssnano = require('cssnano');
const imagemin = require('gulp-imagemin');
const pixrem = require('pixrem');
const plumber = require('gulp-plumber');
const postcss = require('gulp-postcss');
const reload = browserSync.reload;
const rename = require('gulp-rename');
const sass = require('gulp-sass')(require('sass'));
const spawn = require('child_process').spawn;
const uglify = require('gulp-uglify-es').default;
const npmdist = require("gulp-npm-dist");


// Relative paths function
function pathsConfig(appName) {
    this.app = `./${pjson.name}`;
    const vendorsRoot = 'node_modules';

    return {
        vendorsJs: [
            `${vendorsRoot}/@popperjs/core/dist/umd/popper.js`,
            `${vendorsRoot}/bootstrap/dist/js/bootstrap.js`,
            `${vendorsRoot}/prismjs/prism.js`,
            `${vendorsRoot}/prismjs/plugins/normalize-whitespace/prism-normalize-whitespace.js`,
            `${vendorsRoot}/iconify-icon/dist/iconify-icon.min.js`,
            `${vendorsRoot}/swiper/swiper-bundle.min.js`,
            `${vendorsRoot}/simplebar/dist/simplebar.min.js`,
            `${vendorsRoot}/apexcharts/dist/apexcharts.min.js`,
            `${vendorsRoot}/choices.js/public/assets/scripts/choices.min.js`,
            `${vendorsRoot}/clipboard/dist/clipboard.min.js`,
            `${vendorsRoot}/gumshoejs/dist/gumshoe.polyfills.js`,
            `${vendorsRoot}/toastify-js/src/toastify.js`,
            `${vendorsRoot}/moment/moment.js`,
            `${vendorsRoot}/flatpickr/dist/flatpickr.js`,
            `${vendorsRoot}/vanilla-wizard/dist/js/wizard.min.js`,
            `${vendorsRoot}/inputmask/dist/inputmask.min.js`,
            `${vendorsRoot}/nouislider/dist/nouislider.min.js`,
        ],
        app: this.app,
        templates: `${this.app}/templates`,
        css: `${this.app}/static/css`,
        scss: `${this.app}/static/scss`,
        fonts: `${this.app}/static/fonts`,
        images: `${this.app}/static/images`,
        js: `${this.app}/static/js`,
    };
}

const paths = pathsConfig();

////////////////////////////////
// Tasks
////////////////////////////////

// Styles autoprefixing and minification
function styles() {
    const processCss = [
        autoprefixer(), // adds vendor prefixes
        pixrem(), // add fallbacks for rem units
    ];

    const minifyCss = [
        cssnano({preset: 'default'}), // minify result
    ];

    return src([`${paths.scss}/app.scss`, `${paths.scss}/icons.scss`])
        .pipe(
            sass({
                importer: tildeImporter,
                includePaths: [paths.scss],
            }).on('error', sass.logError),
        )
        .pipe(plumber()) // Checks for errors
        .pipe(postcss(processCss))
        .pipe(dest(paths.css))
        .pipe(rename({suffix: '.min'}))
        .pipe(postcss(minifyCss)) // Minifies the result
        .pipe(dest(paths.css));
}

// Javascript minification
function scripts() {
    return src([`${paths.js}/app.js`, `${paths.js}/config.js`, `${paths.js}/layout.js`])
        .pipe(plumber()) // Checks for errors
        .pipe(uglify()) // Minifies the js
        .pipe(rename({suffix: '.min'}))
        .pipe(dest(paths.js));
}

// Vendor Javascript minification
function vendorScripts() {
    return src(paths.vendorsJs, {sourcemaps: true})
        .pipe(concat('vendors.js'))
        .pipe(dest(paths.js))
        .pipe(plumber()) // Checks for errors
        .pipe(uglify()) // Minifies the js
        .pipe(rename({suffix: '.min'}))
        .pipe(dest(paths.js, {sourcemaps: '.'}));
}

const plugins = function () {
    const out = paths.app + "/static/vendor/";
    return src(npmdist(), {base: "./node_modules"})
        .pipe(rename(function (path) {
            path.dirname = path.dirname.replace(/\/dist/, '').replace(/\\dist/, '');
        }))
        .pipe(dest(out));
};


// Image compression
function imgCompression() {
    return src(`${paths.images}/*`)
        .pipe(imagemin()) // Compresses PNG, JPEG, GIF and SVG images
        .pipe(dest(paths.images));
}

// Run django server
function runServer(cb) {
    const cmd = spawn('python', ['manage.py', 'runserver'], {stdio: 'inherit'});
    cmd.on('close', function (code) {
        console.log('runServer exited with code ' + code);
        cb(code);
    });
}

// Browser sync server for live reload
function initBrowserSync() {
    browserSync.init(
        [`${paths.css}/*.css`, `${paths.js}/*.js`, `${paths.templates}/*.html`],
        {
            // https://www.browsersync.io/docs/options/#option-proxy
            proxy: {
                target: '127.0.0.1:8000',
                proxyReq: [
                    function (proxyReq, req) {
                        // Assign proxy 'host' header same as current request at Browsersync server
                        proxyReq.setHeader('Host', req.headers.host);
                    },
                ],
            },
        },
    );
}

// Watch
function watchPaths() {
    watch(`${paths.scss}/**/*.scss`, styles);
    watch(`${paths.templates}/**/*.html`).on('change', reload);
    watch([`${paths.js}/**/*.js`, `!${paths.js}/**/*.min.js`], scripts).on(
        'change',
        reload,
    );
}

// Generate all assets
const generateAssets = parallel(styles, scripts, vendorScripts, plugins, imgCompression);

// Set up dev environment
const dev = parallel(watchPaths);

exports.default = series(generateAssets, dev);
exports['generate-assets'] = generateAssets;
exports['dev'] = dev;
