function getQueryParams()
{
    var vars = {}, hash;
    var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
    for(var i = 0; i < hashes.length; i++)
    {
        hash = hashes[i].split('=');
        vars[hash[0]] = hash[1];
    }
    return vars;
}

function DumpObjectIndented(obj, indent)
{
  var result = "";
  if (indent == null) indent = "";

  for (var property in obj)
  {
    var value = obj[property];
    if (typeof value == 'string')
      value = "'" + value + "'";
    else if (typeof value == 'object')
    {
      if (value instanceof Array)
      {
        // Just let JS convert the Array to a string!
        value = "[ " + value + " ]";
      }
      else
      {
        // Recursive dump
        // (replace "  " by "\t" or something else if you prefer)
        var od = DumpObjectIndented(value, indent + "  ");
        // If you like { on the same line as the key
        //value = "{\n" + od + "\n" + indent + "}";
        // If you prefer { and } to be aligned
        value = "\n" + indent + "{\n" + od + "\n" + indent + "}";
      }
    }
    result += indent + "'" + property + "' : " + value + ",\n";
  }
  return result.replace(/,\n$/, "");
}

var WCRefresh = function(e) {
  var data = getQueryParams();
  $.ajax({
    url: "/recent_operations/",
    type: 'get',
    dataType: 'json',
    data: data,
    success: function(d){
      if (d.operations.length) {
	for (var i = d.operations.length-1; i >= 0; i--) {
	  // TODO: compare/update
	  var el = d.operations[i];
	  var r = $("<tr></tr>");
	  r.addClass(i % 2 ? "even" : "odd");
	  r.append($("<td></td>")
		   .append($("<div class=\"operation_status\"></div>").addClass(el.status)));
	  r.append("<td>" + el.action + "</td>");

	  // link to video
	  r.append("<td>" + el.video_title + "</td>");

	  // link to series
	  r.append("<td>" + el.series_title + "</td>");
	  r.append("<td>" + el.modified + "</td>");
	  $("#operations tbody").prepend(r);
        }
	// TODO: make sure table has max 200 items
      } else {
	// nothing returned
	// should notify the user
      }
//      setTimeout(WCRefresh, 3000);
    }
  });
};


jQuery(function($){
    // Ensure that the CSRF token is sent with AJAX POSTs sent by jQuery
    // Taken from the documentation: http://docs.djangoproject.com/en/dev/ref/contrib/csrf/
    $('html').ajaxSend(function(event, xhr, settings) {
        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie != '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) == (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        if (!(/^http:.*/.test(settings.url) || (/^https:.*/.test(settings.url)))) {
            // Only send the token to relative URLs i.e. locally.
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    });

   $(document).ready(
     function() {
       WCRefresh();
     }
   );
});
