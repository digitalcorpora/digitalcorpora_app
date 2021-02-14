<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <style type="text/css" media="screen">@import url( https://digitalcorpora.org/wp/wp-content/themes/digitalcorpora/style.css );</style>
    <link rel='stylesheet' id='wp-block-library-css'  href='https://digitalcorpora.org/wp/wp-includes/css/dist/block-library/style.min.css?ver=5.6.1' type='text/css' media='all' />
    <link rel='stylesheet' id='contact-form-7-css'  href='https://digitalcorpora.org/wp/wp-content/plugins/contact-form-7/includes/css/styles.css?ver=5.3.2' type='text/css' media='all' />
    <link rel='stylesheet' id='simple-banner-style-css'  href='https://digitalcorpora.org/wp/wp-content/plugins/simple-banner/simple-banner.css?ver=2.9.4' type='text/css' media='all' />
    <link rel='stylesheet' id='jvcf7p_client_css-css'  href='https://digitalcorpora.org/wp/wp-content/plugins/jquery-validation-for-contact-form-7-pro/includes/assets/css/jvcf7p_client.css?ver=5.2' type='text/css' media='all' />
    <script type='text/javascript' src='https://digitalcorpora.org/wp/wp-includes/js/jquery/jquery.min.js?ver=3.5.1' id='jquery-core-js'></script>
    <script type='text/javascript' src='https://digitalcorpora.org/wp/wp-includes/js/jquery/jquery-migrate.min.js?ver=3.3.2' id='jquery-migrate-js'></script>
    <script type='text/javascript' id='simple-banner-script-js-extra'></script>
    <title>Digital Corpora Downloads: {{prefix}}</title>

    <style type="text/css">
      .post h1 { padding: 0 0 10px 0; }
      .post h2 { padding: 0 0 5px 0;  }
      .post h3 { padding: 10px 0 5px 0; font-size: 12pt;}
      .post .content td.r { text-align: right;}
      .post .content td.c { text-align: center;}
      .post .content li.subdir { font-size: 12pt;}
    </style>
  </head>
  <body class='customize-support'>
    <div id='wrap'>
      <div id='container'>
	<div id="header">
	  <div id="caption">
	    <h1 id="title"><a href="https://digitalcorpora.org/">Digital Corpora</a></h1>
	    <div id="tagline">Producing the Digital Body</div>
	  </div>
	  <div class="fixed"></div>
	</div>
	<div id="navigation">
	  <!-- menus START -->
	  <ul id="menus">
	    <li class="page_item"><a class="home" title="Home" href="http://digitalcorpora.org/">Home</a></li>

            % for path in paths:
                <li class="page_item"><a href="/{{path[0]}}">{{path[1]}}</a></li>
            % end
            <!-- loop here c1 -->
	  </ul>
	</div>

	<!-- searchbox START -->
	<div id="searchbox">
	  <form action="https://digitalcorpora.org" method="get">
	    <div class="content">
	      <input type="text" class="textfield" name="s" size="24" value="" />
	      <input type="submit" class="button" value="" />
	    </div>
	  </form>
	</div>

	<div class="fixed"></div>
	<div id='content'>
	  <div id='main'>
	    <div class='post'>
	      <div class='content'>
		<h1>downloads.digitalcorpora.org S3 Browser</h1>
		<h2><!--
            % for path in paths:
            -->/<a href="{{path[0]}}">{{path[1]}}</a><!--
            % end
            --> sub-dirs:</h2>

                <ul>
                  % for d in dirs:
                      <li class='subdir'><a href='{{d}}'>{{d}}</a></li>
                  % end
                </ul>
		<h2><!--
            % for path in paths:
            -->/<a href="{{path[0]}}">{{path[1]}}</a><!--
            % end
            --> files:</h2>
		<table>
		  <thead>
		    <tr><th>Name</th><th>Size</th><th>SHA2-256</th><th>SHA3-256</th></tr>
		  </thead>
		  <tbody>
                    % for f in files:
                    <tr>
                      <td><a href='{{f[0]}}'>{{f[1]}}</a></td>
                      <td class='r'>{{f[2]}}</td><td class='c'>{{f[3]}}</td>
                      <td class='c'>{{f[4]}}</td>
                    </tr>
                    % end
		  </tbody>
		  <tfoot>
		  </tfoot>
		</table>
	      </div>
	    </div>
	  </div>
	  <!-- end of content -->
	</div>

	<div class="fixed"></div>
	<!-- footer START -->
	<div id="footer">
	  <a id="gotop" href="#" onclick="MGJS.goTop();return false;">Top</a>
	  <a id="powered" href="http://wordpress.org/">WordPress</a>
	  <div id="copyright">
	    Copyright &copy; 2009-2021 Digital Corpora	</div>
	  <div id="themeinfo">
	    Theme by <a href="http://www.neoease.com/">NeoEase</a>.
            Valid <a href="http://validator.w3.org/check?uri=referer">XHTML 1.1</a>
            and <a href="http://jigsaw.w3.org/css-validator/check/referer?profile=css3">CSS 3</a>.
	  </div>
	</div>
	<!-- footer END -->
      </div>
    </div>
  </body>
</html>
