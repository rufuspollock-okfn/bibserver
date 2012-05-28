#!/usr/bin/perl -w -I/usr/sbin 
# Marc21 to BIBJSON  conversion script
# Written by Ed Chamberlain, Cambridge Univesity Library 2012
# Produced for the Open bibliography 2 project


#TO DO:
# Check output
# Fix 856 issue
# Consider subject heading provision / loop for ntoes
# Spin out config to CSV ?

#BIBJSON example collection - target data output
#{
#    "metadata": {
#        "_id": "my_collection",
#        "label": "My collection of records",
#        "owner": "test",
#        "query": "http://bibsoup.net/test/my_collection.json?",
#        "created": "2011-10-31T16:05:23.055882",
#        "modified": "2011-10-31T16:05:23.055882",
#        "from": 0,
#        "size": 2,
#        "source": "http://webaddress.com/collection.bib",
#        "records": 1594,
#        "namespace": {
#            "dc": "http://purl.org/dc/terms"
#        }
#    },
#    "records": [
#        {
#            "author":[{"name":"Mark MacGillivray","id":"sumid"}],
#            "title":"How to do BibJSON",
#            "year":"2012",
#            "collection": "my_collection"
#        },
#        {
#            "title": "another great book",
#            "collection": "my_collection",
#            "dc:creator": "Mark MacGillivray",
# "      identifiers":[
#        {
#       "id": "0002-9327",
#       "type": "issn"
#          "links": [
#        {
#            "url": "http://bibsoup.net",
#            "anchor": "Go to BibSoup"
#        }
#    ]
#        }
#      }
#    ]
#}


use Switch;
use MARC::Record;
use MARC::File::USMARC;
use Data::Dumper;
use Scalar::Util;
use Digest::MD5 qw(md5 md5_hex md5_base64);
use Getopt::Std;
use JSON;
use utf8;

#use strict;
#we can safely turn off these warnings
no warnings "uninitialized";
#log file
open (LOG, "> log.txt") or die "could not open log: $!";
open (TMP, "> tmp.txt") or die "could not open temp file: $!";

#./marc2bibjson_batch2.pl < small_sample.mrc > sample_output.js
my $enable = 'true';
my ($marcFile,$outputFilename,$tmpFilename);

if ($ARGV[1] eq '-bibserver') {
           print STDOUT '{"display_name": "MARC",
                    "format": "marc21",
                    "contact": "Edmund Chamberlain emc59@cam.ac.uk",
                    "bibserver_plugin": true
                   }
                   ';      
    }

if (STDIN) {
         
# Why is this necessary? MARC::File cannot seemingly accept STDIN as either file handle or direct input, needs a file path/name ...
     while (<>) {
     print TMP $_;         
    }
close TMP;



         #print LOG "$marcFile";
         my %outPut=();
         my @records=''; 
         my $count=0;
         my $inFile=MARC::File::USMARC->in('tmp.txt');
           
                  while (my $record=$inFile->next()){
                           my %exportRecord = convertRecord($record);
                           push(@records,\%exportRecord);
                           $count++;
                         }
                         
                  #end record loop        
                  $outPut{"records"} = \@records;
                 
                  my @metadata =(
                      'source' => "$marcFile",
                      'records' => "$count",
                      'namespace' => (
                                    'dc' => "http://purl.org/dc/terms"
                                    
                     )             
                   );
         
           
         $outPut{'metadata'}= \@metadata;
        
         # write json output
         my $json = new JSON;
         $json = $json->utf8([$enable]);
         $json = $json->pretty([$enable]);
         
         print STDOUT $json->encode(\%outPut);
  #       print STDOUT $json->encode(\@records);
         print LOG "$count records converted \n";
         
         
         # Curl over JSON to bibserver with API key in URL ...
         # http://bibsoup.net/upload?source=http://MYUPLOAD.com/filename.bib&format=json&collection=MYCOLLECTION
}else{
  print "reads STDIN as marc input - writes to STDOUT \n";
}
         
###############

sub convertRecord {
         my $record = shift;
         my %exportRecord =();
         
         
                #  print "\n ########## \n";
                #  print Dumper($record);
                #  print "\n ########## \n";
                  
                 ############ Format ############
                  my $format='';
                  # read header - case on format code for type
                  my $formatCode = substr($record->leader,6,1);
                  switch ($formatCode) {
                                        case /[at]/    {$format='text';}
                                        case /[dfpt]/  {$format='manuscript';}
                                        case /[am]/    {$format='book';}
                                        case  'm'      {$format='software';}
                                        case /[bis]/   {$format='journal';}
                                        case /[g]/     {$format='video';}
                                        case /[ji]/    {$format='music';}
                                        case /[e]/     {$format='map';}
                           }
                  $exportRecord{'format'} = $format;

                  
                  #Library of Congress Classification
                   if ($record->field('050')) {
                         $exportRecord{"libraryOfCongressCallNo"} = trim($record->field('050')->as_string("a"));
                  }
                  
                   #Dewey
                   if ($record->field('080')) {
                         $exportRecord{"universalDecimalClassificationNo"} = trim($record->field('080')->as_string("a"));
                  }
                  
                  
                  #Dewey
                   if ($record->field('082')) {
                         $exportRecord{"deweyDecimalCallNo"} = trim($record->field('082')->as_string("a"));
                  }

                  ############ Identifiers ############
                  
                  my @identifiers =();
         
                  if ($record->field('001')) {
                    my %local = ('id' => $record->field('001')->data(), 'type' => 'local');       
                    push(@identifiers,\%local);       
                  }
                  
                  if ($record->field('020')) {
                    my %isbn = ('id' => $record->field('020')->as_string("a"), 'type' => 'isbn');       
                    push(@identifiers,\%isbn);       
                  }
                  
                  if ($record->field('022')) {
                    my %issn = ('id' => $record->field('022')->as_string("a"), 'type' => 'issn');       
                    push(@identifiers,\%issn);       
                  }
                  
                     if ($record->field('010')) {
                    my %lccn = ('id' => $record->field('010')->as_string("a"), 'type' => 'lccn');       
                    push(@identifiers,\%lccn);       
                  }
                  
                       if ($record->field('035')) {
                    my %oclc = ('id' => $record->field('035')->as_string("a"), 'type' => 'OCLC');       
                    push(@identifiers,\%oclc);       
                  }
                       
                       if ($record->field('015')) {
                    my %lccn = ('id' => $record->field('015')->as_string("a"), 'type' => 'National Bibliography');       
                    push(@identifiers,\%lccn);       
                  }
                       
                       
                  
                  if (@identifiers) {
                     $exportRecord{'identifiers'} = \@identifiers;       
                  }
                  
                 ############### Links ############## - not working - blessed variable issue
                 if ($record->field('856')) {
                   #To explicit?
                   my @exportLinks =();
                   my %exportLink = ();
                   my $link ='';
                                 my @links =  $record->field('856');
                                 foreach $link(@links) {
                                  
                              # print Dumper($link);s
                                  my %exportLink = ('url' => $link->as_string("u"), 'anchor' => $link->as_string("z"));
                                   # print Dumper(\%exportLink);
                                  push(@exportLinks,\%exportLink);             
                                 }
                                 
                           if (@exportLinks) {
                              $exportRecord{'links'} = \@exportLinks;       
                           }
                  }
                 ############ Misc. fields based on QDC, attempting to target core Open Bib concept of non copyrightable data elements ########
                  
                  if ($record->field('245')) {
                         $exportRecord{"title"} = trim($record->field('245')->as_string("abnp"));
                  }
                  
                  if ($record->field('240')) {
                         $exportRecord{"alternativeTitle"} = trim($record->field('240')->as_string("adfgklmnoprst"));
                  }
                  
                  if ($record->field('260')) {
                         $exportRecord{"publisher"} = trim($record->field('260')->as_string("b"));
                  }
                  
                  
                   if ($record->field('046')) {
                         $exportRecord{"dateCreated"} = trim($record->field('046')->as_string("k"));
                  }
       
                   if ($record->field('046')) {
                         $exportRecord{"dateModified"} = trim($record->field('046')->as_string("k"));
                  }
                  
                  if ($record->field('260')) {
                         $exportRecord{"dateIssued"} = trim($record->field('260')->as_string("c"));
                  }
                  
                  if ($record->field('300')) {
                         $exportRecord{"extent"} = trim($record->field('300')->as_string("a"));
                  }
                  
                  if ($record->field('340')) {
                         $exportRecord{"medium"} = trim($record->field('340')->as_string("a"));
                  }
                  
                  if ($record->field('500')) {
                         $exportRecord{"description"} = trim($record->field('500')->as_string());
                  }
                   if ($record->field('505')) {
                         $exportRecord{"tableOfContents"} = trim($record->field('505')->as_string());
                  }
                   
                   if ($record->field('513')) {
                         $exportRecord{"temporial"} = trim($record->field('513')->as_string("b"));
                  }
                   
                   if ($record->field('520')) {
                         $exportRecord{"abstract"} = trim($record->field('520')->as_string("a"));
                  }
                   
                   if ($record->field('522')) {
                         $exportRecord{"spatial"} = trim($record->field('522')->as_string("a"));
                  }
                  
                   if ($record->field('540')) {
                         $exportRecord{"accessRights"} = trim($record->field('540')->as_string());
                  }
                   
                    if ($record->field('546')) {
                         $exportRecord{"languageNote"} = trim($record->field('546')->as_string("a"));
                  }
                   
                   
                    if ($record->field('490')) {
                         $exportRecord{"isPartOf"} = trim($record->field('490')->as_string());
                  }
                    
                    if ($record->field('653')) {
                             my @localSubjects = $record->field('653');
                             my @exportLocals=();
                           foreach my $localSubject(@localSubjects) {
                           my $exportSubject = $localSubject->as_string('a b c d e f h j k l m n o p q r s t');
                             push(@exportLocals,$exportSubject); 
                           }
                   $exportRecord{'subjects'} = \@exportLocals;     
                  }
                    
                   if ($record->field('650')) {
                         
                       my @subjects = $record->field('650');
                       my @exportMESHs=();
                       my @exportLCSHs=();
                         
                         # loop 650's with clause for 
                           foreach my $subject(@subjects) {
                                    
                                my  $subjectField=$subject->as_string('a b c d e f h j k l m n o p q r s t');
         
                                    # additional clauses for qualifiers
                                    if ($subject->subfield('v')) {
                                       $subjectField .= " -- " . $subject->subfield('v');
                                    }
                                    if ($subject->subfield('x')) {
                                      $subjectField .= " -- " . $subject->subfield('x');
                                    }
                                    if ($subject->subfield('y')) {
                                      $subjectField .= " -- " . $subject->subfield('y');
                                    }
                                    if ($subject->subfield('z')) {
                                      $subjectField .= " -- " . $subject->subfield('z');
                                    }    
                                    
                               if ($subject->indicator(2) eq '0') {    
                                       # my $exportsubjectLCSH = trim($subject->as_string('a'));
                                         push(@exportLCSHs,$subjectField);
                               }
                                        
                                elsif ($subject->indicator(2) eq '2') {
                                      #  my $exportsubjectMESH = trim($subject->as_string('a'));
                                         push(@exportMESHs,$subjectField);      
                               }
                           }
                   
                        # Push to records 
                           if (@exportLCSHs > 0) {
                                $exportRecord{'subjectsLCSH'}    = \@exportLCSHs;    
                           }     
                           
                           
                            if (@exportMESHs > 0) {
                             $exportRecord{'subjectsMESH'}    = \@exportMESHs;    
                           }
                   
                   }
                  
                  
                  if ($record->field('773')) {
                         $exportRecord{"isPartOf"} = trim($record->field('773')->as_string('n'));
                  }    
                  
                   if ($record->field('774')) {
                         $exportRecord{"hasPart"} = trim($record->field('774')->as_string('n'));
                  }
                   
                   if ($record->field('510')) {
                         $exportRecord{"isReferencedBy"} = trim($record->field('510')->as_string('a'));
                  } 
                  
                   if ($record->field('538')) {
                         $exportRecord{"requires"} = trim($record->field('538')->as_string('a'));
                  } 
                  
         
                  
                  # Needs indicator 2
                  # if ($record->field('650')) {
                  #       $exportRecord{"subjectMesh"} = trim($record->field('653')->as_string('a'));
                  #}     

                   if ($record->field('786')) {
                         $exportRecord{"source"} = trim($record->field('786')->as_string('n'));
                  }  

##################
                    
################## Author needs to be a sub into which we can feed: 720$a (creator) , 110 $a corp author, 700 1$a - added entry - personal name 710 2$a added entry corp name
                  
                   my @exportAuthors=();
                  
                   
                   my @authors =();
                   my $eachAuthor ='';
                   
                   if ($record->field('100')) {
                        
                           @authors = $record->field('100');
                           
                           foreach $eachAuthor(@authors)  {
                                    my %exportAuthor =();
                                    my $authorFull = trim($eachAuthor->subfield('a'));
                                   
      
                                    $exportAuthor{'name'} = $authorFull;
                                    
                                     my @parsed_author=split(/,/, $authorFull);
                                    
                                    $exportAuthor{'lastname'} = $parsed_author[0];
                                    
                                    $exportAuthor{'firstname'} = $parsed_author[1];
                                 
                                    my $dates = $eachAuthor->subfield('d');
                                   
                                   my ($birthDate,$deathDate);
                                    
                          # The glorious 100$d disassembled ...
                                    if ($dates) {
                                                     #first of all, get rid of ca. and fl. which aren't real birth or death dates
                                                     if ($dates=~/fl\.|ca\./){
                                                              #do nothing
                                                     }
                                                     #otherwise, if date contains a hyphen, assume range
                                                     #but fix also works for unterminated dates?
                                                     elsif ($dates=~/\-/) {
                                                              
                                                              my @dates=split(/\-/,$dates);
                                                              $exportAuthor{'birthDate'} = trim($dates[0]);
                                                              
                                                              if ($dates[1]) {
                                                                      $exportAuthor{'deathDate'} = trim($dates[1]);
                                                              }
                                                              
                                       #No Hyphen - assume single date - look for definitive birth event with a 'd' ...
                                                     } elsif ($dates=~/\b\./) {
                                                              
                                                               $exportAuthor{'birthDate'} = trim($dates[0]);
                                                              
                                       # - look for definitive death event with a 'd' ...
                                                     } elsif ($dates=~/\d\./) {
                                                              
                                                              $exportAuthor{'deathDate'} = trim($dates[0]);
                                       # Final assumption for authors with recorded dates but with single date no hyphen. Assume its a birthdate?
                                                     } else {
                                                              $exportAuthor{'birthDate'} = trim($dates[0]);
                                                     }
                                       # produce output for dates ...
                                    }
                        
                        # Assemble author object           
                        push(@exportAuthors,\%exportAuthor);
                        
                        
                        # End author loop
                        }
                 # Add list of authors to export object             
                $exportRecord{'author'} = \@exportAuthors;           
                }   
                      
return %exportRecord;           
}


sub genGuidString {
      my $string = shift;
      $string =~ s/[^a-zA-Z0-9-\s]//g;  
       return md5_hex(encode_utf8($string));    
}

sub scrubAlpha($) {
     my $string = shift;
     $string =~ s/\D//g;   
    return $string;     
}

#Generic whitespace killer,
#plus strips trailing punctuation
sub trim{
        my $string = shift;
        #strips some of the punctuation off the end
        $string=~s/[\.\;\/\:\,]$//;
        #and then strip any remaining whitespace
	$string =~ s/^\s+//;
	$string =~ s/\s+$//;
	return $string;
}

sub clean{
         my $string=shift;
         $string=~s/([\"\t\n\\])/\\$1/g;
         return $string;
}
