gdprgeopopupInit();

function gdprgeopopupInit() {
    jQuery(document).ready(function () {
        var el = jQuery('.gdpr-geopopup-wrap');
        if (!el || !el.length)
            return;

        var gdprGeoPopups = localStorage.getItem('gdprgeopopups');
        gdprGeoPopups = JSON.parse(gdprGeoPopups);

        if (gdprGeoPopups && gdprGeoPopups.length) {
            if (gdprGeoPopups.indexOf(gdprGeoPopupConfig.popupId) > -1) {
                el.remove();
                jQuery('.gdpr-geopopup-curtain').remove();
            }
        } else {
            el.css({'opacity': 1});
            jQuery('.gdpr-geopopup-curtain').css({'opacity': '0.7'});

            gdprGeoPopups = [];
        }

        jQuery('a', el).css('color', gdprGeoPopupConfig.textColor);
        gdprgeopopupSetResponsiveStyles();
        jQuery(window).resize(function () {gdprgeopopupSetResponsiveStyles()})

        jQuery('.gdpr-geopopup-tos-link').click(function (e) {
            e.preventDefault();

            jQuery('.gdpr-geopopup-mainformwrap').hide();
            jQuery('.gdpr-geopopup-tosformwrap').show();
        })

        jQuery('.gdpr-geopopup-back-button').click(function (e) {
            e.preventDefault();

            jQuery('.gdpr-geopopup-mainformwrap').show();
            jQuery('.gdpr-geopopup-tosformwrap').hide();
        })


        jQuery('.gdpr-geopopup-agreetos-button').click(function (e) {
            e.preventDefault();

            jQuery('#gdpr-geopopup-checkbox-s').prop('checked', true);
            jQuery('.gdpr-geopopup-mainformwrap').show();
            jQuery('.gdpr-geopopup-tosformwrap').hide();
        })

        jQuery('#gdpr-geopopup-formdata').submit(function (e) {
            //e.preventDefault();
            var errorDiv = jQuery(".gdpr-geopopup-validation-errors");
            errorDiv.html('');

            var errors = gdprgeopopupValidate();

            if (errors.length) {
                e.preventDefault();

                errors.forEach(function (err) {
                    errorDiv.append("<p>"+err+"</p>");
                })
            } else {
                gdprGeoPopups.push(gdprGeoPopupConfig.popupId);
                localStorage.setItem('gdprgeopopups', JSON.stringify(gdprGeoPopups));
            }
        });

        jQuery('.gdpr-geopopup-close-popup, .gdpr-geopopup-close-popup-button').click(function (e) {
            e.preventDefault();

            var gdprGeoPopups = localStorage.getItem('gdprgeopopups');
            gdprGeoPopups = JSON.parse(gdprGeoPopups);

            if (!gdprGeoPopups || !gdprGeoPopups.length) {
                gdprGeoPopups = [];
            }

            gdprGeoPopups.push(gdprGeoPopupConfig.popupId);
            localStorage.setItem('gdprgeopopups', JSON.stringify(gdprGeoPopups));

            el.remove();
            jQuery('.gdpr-geopopup-curtain').remove();
        })
    })
}

function gdprgeopopupValidate() {
    var errors = [];

    var firstName = jQuery("#gdpr-geopopup-first_name").val();
    var lastName = jQuery("#gdpr-geopopup-last_name").val();
    var email = jQuery("#gdpr-geopopup-email").val();
    var consent = jQuery("#gdpr-geopopup-checkbox-s").val();


    if (!firstName)
        errors.push('First name is required');

    if (!lastName)
        errors.push('Last name is required');

    if (!email) {
        errors.push('Email is required');
    } else if (!gdprgeopopupValidateEmail(email)) {
        errors.push('Valid email is required');
    }

    return errors;
}

function gdprgeopopupValidateEmail(email) {
    var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(email);
}

function gdprgeopopupSetResponsiveStyles() {
    var el = jQuery('.gdpr-geopopup-wrap');
    if ((el.height() + 100) > jQuery(window).height()) {
        el.css({
           'position' : 'absolute',
           'top' : '20px',
           'transform' : 'translate(-50%, 0%)'
        });
    } else {
        el.css({
            'position' : 'fixed',
            'top' : '50%',
            'transform' : 'translate(-50%, -50%)'
        });
    }
}