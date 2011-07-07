/* -*- mode: espresso; espresso-indent-level: 2; indent-tabs-mode: nil -*- */
/* vim: set softtabstop=2 shiftwidth=2 tabstop=2 expandtab: */

var connectorTable;
var asInitValsSyn = new Array();


initConnectorTable = function (pid)
{
  var tableid = '#connectortable';

  connectorTable = $(tableid).dataTable(
  {
    // http://www.datatables.net/usage/options
    "bDestroy": true,
    "sDom": '<"H"lr>t<"F"ip>',
    // default: <"H"lfr>t<"F"ip>
    "bProcessing": true,
    "bServerSide": true,
    "bAutoWidth": false,
    "sAjaxSource": 'model/connector.list.php',
    "fnServerData": function (sSource, aoData, fnCallback) {
      
      var skeletonid;
      if(atn !== null) {
        skeletonid = atn.skeleton_id;
      } else {
        skeletonid = 0;
      }

      aoData.push({
        "name": "relation_type",
         "value" : $('#connector_relation_type :selected').attr("value")
      });
      aoData.push({
        "name" : "pid",
        "value" : pid
      });
      aoData.push({
        "name" : "skeleton_id",
        "value" : skeletonid
      });
      $.ajax({
        "dataType": 'json',
        "type": "POST",
        "url": sSource,
        "data": aoData,
        "success": function(data, text) {
          if (data.error ) {
            // hide widget
            document.getElementById('connectortable_widget').style.display = 'none';
            ui.onresize();
            alert( data.error );
            return;
          }
          fnCallback(data);
        }
      });

    },
    "aLengthMenu": [
      [10, 25, 50, -1],
      [10, 25, 50, "All"]
    ],
    "bJQueryUI": true,
    "aoColumns": [
    {
      "bSearchable": false,
      "bSortable": true
    }, // connector id
    {
      "bSearchable": false,
      "bSortable": true
    }, // connectortags
    {
      "bSearchable": false,
      "bSortable": true
    }, // number of nodes
    {
      "bVisible": true,
      "bSortable": true
    } // username
    ]

  });

  $(tableid + " tfoot input").keyup(function ()
  { /* Filter on the column (the index) of this element */
    connectorTable.fnFilter(this.value, $("tfoot input").index(this));
  });

/*
	 * Support functions to provide a little bit of 'user friendlyness' to the textboxes in
	 * the footer
	 */
  $(tableid + " tfoot input").each(function (i)
  {
    asInitValsSyn[i] = this.value;
  });

  $(tableid + " tfoot input").focus(function ()
  {
    if (this.className == "search_init")
    {
      this.className = "";
      this.value = "";
    }
  });

  $(tableid + " tfoot input").blur(function (i)
  {
    if (this.value == "")
    {
      this.className = "search_init";
      this.value = asInitValsSyn[$("tfoot input").index(this)];
    }
  });

  $(tableid + " tbody tr").live('click', function ()
  {

  });

  $('#connector_relation_type').change(function() {
    connectorTable.fnDraw();
  });

}
