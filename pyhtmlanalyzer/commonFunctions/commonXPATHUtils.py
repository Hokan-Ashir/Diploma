__author__ = 'hokan'

class commonXPATHUtils:
    # NOTE if you use xPath 2.0 you can use lower-case() and upper-case() functions, otherwise
    # you should use translate() like this:
    # WARN: only suitable for english characters
    # translate('some text','abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ') for upper-case
    # translate('some text','ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz') for lower-case
    @staticmethod
    def toUpperCase(text, quoteText):
        if quoteText == True:
            return 'translate(\'%s\',\'abcdefghijklmnopqrstuvwxyz\',\'ABCDEFGHIJKLMNOPQRSTUVWXYZ\')' % text
        else:
            return 'translate(%s,\'abcdefghijklmnopqrstuvwxyz\',\'ABCDEFGHIJKLMNOPQRSTUVWXYZ\')' % text

    @staticmethod
    def toLowerCase(text, quoteText):
        if quoteText == True:
            return 'translate(\'%s\',\'ABCDEFGHIJKLMNOPQRSTUVWXYZ\',\'abcdefghijklmnopqrstuvwxyz\')' % text
        else:
            return 'translate(%s,\'ABCDEFGHIJKLMNOPQRSTUVWXYZ\',\'abcdefghijklmnopqrstuvwxyz\')' % text
    #

    # NOTE: there is no end-with() function in xPath 1.0, so you can use something like this:
    # $str2 = substring($str1, string-length($str1)- string-length($str2) +1)
    # will return true and false as result
    @staticmethod
    def endWith(text, endWithText, quoteText, quoteEndWithText):
        if quoteText == True and quoteEndWithText == True:
            return '\'%s\' = substring(\'%s\', string-length(\'%s\') - string-length(\'%s\') + 1)' % (endWithText, text, text, endWithText)
        elif quoteText == False and quoteEndWithText == True:
            return '\'%s\' = substring(%s, string-length(%s) - string-length(\'%s\') + 1)' % (endWithText, text, text, endWithText)
        elif quoteText == True and quoteEndWithText == False:
            return '%s = substring(\'%s\', string-length(\'%s\') - string-length(%s) + 1)' % (endWithText, text, text, endWithText)
        else:
            return '%s = substring(%s, string-length(%s) - string-length(%s) + 1)' % (endWithText, text, text, endWithText)
    #