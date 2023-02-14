<!DOCTYPE html>
<html lang='en'>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="google" content="notranslate"/>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"
	    integrity="sha256-/xUj+3OJU5yExlq6GSYGSHk7tPXikynS7ogEvDej/m4="
	    crossorigin="anonymous"></script>

    <script type='text/javascript' src='reports.js'></script>
    <link rel='stylesheet' id='wp-block-library-css'  href='https://digitalcorpora.org/wp-includes/css/dist/block-library/style.min.css?ver=5.6.1' type='text/css' media='all' />
    <style type="text/css" media="screen">@import url( https://digitalcorpora.org/wp-content/themes/digitalcorpora/style.css );</style>
    <title>Digital Corpora Reports 2</title>

    <style type="text/css">
      .post h1 { padding: 0 0 10px 0; }
      .post h2 { padding: 0 0 5px 0;  }
      .post h3 { padding: 10px 0 5px 0; font-size: 12pt;}
      .post .content td.name { text-align: left; width:300px;}
      .post .content td.size { text-align: right;}
      .post .content td.hash { text-align: left; word-break: break-all; font-size: 9pt}
      .post .content li.subdir { font-size: 12pt;}
    </style>
  </head>
  <body lang='en-US' class='customize-support'>
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
		<h1>digitalcorpora.org Reports</h1>
		<h2>Available Reports:</h2>
                <ul>
                  % for (ct,r) in enumerate(reports):
                      <li><a href='?report={{ct}}'>{{r}}</a></li>
                  % end
                </ul>
                <div id='report'>
	      </div>
	    </div>
	  </div>
	  <!-- end of content -->
	</div>

	<div class="fixed"></div>
	<!-- (W) footer START -->
	<div id="footer">
	  <a id="gotop" href="#" onclick="MGJS.goTop();return false;">Top</a>
	  <a id="powered" href="http://wordpress.org/">WordPress</a>
	  <div id="copyright">
	    Copyright &copy; 2009-2022 Digital Corpora	</div>
          <p>
          <small>
            Reports provided by <a href='https://github.com/digitalcorpora/app'>s3_reports.py</a>
            Python version {{sys_version}}
          </small>
        </p>
	</div>
	<!-- footer END -->
      </div>
      <!-- This is under the light gray box, in the dark gray box -->
    </div>
  </body>
</html>
