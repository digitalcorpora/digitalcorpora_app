<!DOCTYPE html>
<html lang='en'>
  <head>
    <title>Digital Corpora: {{prefix}}</title>
    <link rel="stylesheet" id="ultra-style-css" href="https://digitalcorpora.org/wp-content/themes/ultra/style.css?ver=1.6.4" type="text/css" media="all">
    <link rel="stylesheet" id="font-awesome-css" href="https://digitalcorpora.org/wp-content/themes/ultra/font-awesome/css/font-awesome.min.css?ver=4.7.0" type="text/css" media="all">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="google" content="notranslate"/>
    <style type="text/css" media="screen">@import url( https://digitalcorpora.org/wp-content/themes/digitalcorpora/style.css );</style>
    <script type='text/javascript' src='https://digitalcorpora.org/wp-includes/js/jquery/jquery.min.js?ver=3.5.1' id='jquery-core-js'></script>

    <style type="text/css">
      body {padding-left: 50pt;}
      a:visited {color:blue;}
      a:link {color:blue;}
      a:hover {color:pink;}
      h1 { padding: 0 0 0 0; margin:0 0 0 0; line-height:normal;}
      h2 { padding: 0 0 0 0; margin:0 0 0 0; line-height:normal;}
      h3 { padding: 0 0 0 0; margin:0 0 0 0; font-size: 12pt; line-height:normal;}
      ul { padding: 20pt 0 20pt 20pt; margin:0 0 0 0; line-height:normal;}
      li { padding: 0 0 0 0; margin:0 0 0 0; line-height:normal;}
      #files th { padding: 0 5pt 0 5pt; }
      #files td { padding: 0 5pt 0 5pt; }
      #files td.name { text-align: left; width:200px; }
      #files td.size  { text-align: right; width:100px}
      #files td.mtime { text-align: left; width:200px; }
      #files td.hash { text-align: left; word-break: break-all; font-size: 9pt; font-family: monospace; width: 44em;}
      #files li.subdir { font-size: 12pt;}
      #files { color:black; }
    </style>
  </head>
  <body lang='en-US' style='background:white'
        class='home page-template-default page page-id-2 logged-in admin-bar full group-blog sidebar tagline no-touch page-layout-default resp customize-support'  >
    <header id="masthead" class="site-header sticky-header scale responsive-menu" style="position: relative; left: auto; width: 100%;">
      <div class="container">
	<div class="site-branding-container">
	  <div class="site-branding">
	    <a href="https://digitalcorpora.org/" rel="home">
	      <h1 class="site-title">Digital Corpora</h1>
	    </a>
	    <p class="site-description">Producing the Digital Body</p>
	  </div><!-- .site-branding -->
	</div><!-- .site-branding-container -->
    </header>

    <!-- legacy searchbox Start -->
    <div id="searchbox">
      <form action="https://digitalcorpora.org" method="get">
	<div class="content">
	  <input type="text" class="textfield" name="s" size="24" value="" />
	  <input type="submit" class="button" value="Search Wordpress Site" />
	</div>
      </form>
    </div>

    <div id='s3_browser'>
      <h1>S3 Downloads Browser</h1>
      <h2><!--
        % for path in paths:
        --><a href="{{path[0]}}">{{path[1]}}</a><!--
        % end
        --> sub-dirs:
      </h2>

      <ul>
        % for d in dirs:
        <li class='subdir'><a href='{{d}}'>{{d}}</a></li>
        % end
      </ul>
      <h2><!--
        % for path in paths:
        --><a href="{{path[0]}}">{{path[1]}}</a><!--
        % end
        --> files:
      </h2>
      <table id='files'>
	<thead>
	  <tr>
            <th>Name</th>
            <th>Size</th>
            <th>Last Modified</th>
            <th><a href='https://digitalcorpora.org/about-digitalcorpora/hashes'>SHA2-256</a></th>
            <th><a href='https://digitalcorpora.org/about-digitalcorpora/hashes'>SHA3-256</a></th>
          </tr>
	</thead>
	<tbody>
          % for f in files:
          <tr>
            <td class='name'><a href='{{f['a']}}'>{{f['basename']}}</a></td>
            <td class='size'>{{f['size']}}</td>
            <td class='mtime'>{{f['LastModified']}}</td>
            <td class='hash'>{{f['sha2_256']}}</td>
            <td class='hash'>{{f['sha3_256']}}</td>
          </tr>
          % end
	</tbody>
	<tfoot>
	</tfoot>
      </table>
    </div> <!-- main -->

    <div id="footer">
      <a id="gotop" href="#" onclick="MGJS.goTop();return false;">Top</a>
      <div id="copyright">
	Copyright &copy; 2009-2022 Simson Garfinkel</div>
      <p>
        <small>
          Directory listing by <a href='https://github.com/digitalcorpora/app'>s3_gateway</a><br/>
          Python version {{sys_version}}
        </small>
      </p>
    </div>
    <!-- footer END -->
    <!-- This is under the light gray box, in the dark gray box -->
  </body>
</html>
