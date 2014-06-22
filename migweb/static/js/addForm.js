function updateElementIndex(el, prefix, ndx) {
    var id_regex = new RegExp('(' + prefix + '-\\d+)');
    var replacement = prefix + '-' + ndx;
    if ($(el).attr("for")) $(el).attr("for", $(el).attr("for").replace(id_regex, replacement));
    if (el.id) el.id = el.id.replace(id_regex, replacement);
    if (el.name) el.name = el.name.replace(id_regex, replacement);
}

function addForm(btn, prefix) {
    var formCount = parseInt($('#id_' + prefix + '-TOTAL_FORMS').val());
    var row = $('.formset-row:last').clone(true).get(0);
    $(row).removeAttr('id').insertAfter($('.formset-row:last')).children('.hidden').removeClass('hidden');
    $(row).children().children().each(function() {
        var elem = $(this);
        if (elem.is('input:checkbox')|| elem.is('input:radio')){
            elem.attr('checked',false);
        }else{
            elem.val('');
        }
        updateElementIndex(this, prefix, formCount);
        $(this).val('');
    });
    $('#id_' + prefix + '-TOTAL_FORMS').val(formCount + 1);
    return false;
}

function addFormDatePicker(btn,form_prefix,field_prefix,field_suffix){
    var formCount = parseInt($('#id_' + form_prefix + '-TOTAL_FORMS').val());
    for(count=0;count<formCount;count++){
        var el="#"+field_prefix+'-'+count+'-'+field_suffix;
        console.log(el)
        $(el).datepicker().on('changeDate',function(){
            $(el).datepicker('hide');
        });
        console.log($(el))
    }
    return false;
}
